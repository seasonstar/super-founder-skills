#!/usr/bin/env npx -y bun

/**
 * Batch Image Generation Script (Qwen / 千问文生图)
 *
 * Generates multiple images from a JSON config file.
 * Supports the unified JSON format (same as web version).
 *
 * Usage:
 *   npx -y bun batch-generate.ts --config slides.json --output-dir ./images
 *
 * Config format (unified with web version):
 *   {
 *     "instruction": "请为我绘制 N 张图片...",
 *     "batch_rules": { "total": N, "one_item_one_image": true, "aspect_ratio": "16:9" },
 *     "style": "完整的 style prompt 字符串...",
 *     "pictures": [
 *       { "id": 1, "topic": "封面", "content": "..." },
 *       { "id": 2, "topic": "...", "content": "..." }
 *     ]
 *   }
 */

import { writeFile, readFile, mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join, dirname, basename } from 'node:path';

// Qwen API endpoint for image generation
const QWEN_API_BASE = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation';
const DEFAULT_MODEL = 'qwen-image-2.0-pro';

// New unified format (same as web version)
interface PictureConfig {
  id: number;
  topic: string;
  content: string;
}

interface BatchRules {
  total: number;
  one_item_one_image?: boolean;
  aspect_ratio?: string;
  do_not_merge?: boolean;
}

interface UnifiedConfig {
  instruction?: string;
  batch_rules?: BatchRules;
  fallback?: string;
  style: string;
  pictures: PictureConfig[];
}

// Legacy format (for backward compatibility)
interface LegacyIllustration {
  id: number;
  prompt: string | object;
  filename: string;
  type?: string;
  position?: string;
}

interface LegacyConfig {
  style?: {
    mode?: string;
    background?: string;
    primary?: string;
    accent?: string[];
  };
  instructions?: string;
  illustrations: LegacyIllustration[];
}

type BatchConfig = UnifiedConfig | LegacyConfig;

interface QwenResponse {
  output?: {
    choices?: Array<{
      finish_reason?: string;
      message?: {
        role?: string;
        content?: Array<{ text?: string; image?: string }>;
      };
    }>;
  };
  usage?: {
    width: number;
    height: number;
    image_count: number;
  };
  request_id?: string;
  status_code?: number;
  code?: string;
  message?: string;
}

function isUnifiedConfig(config: BatchConfig): config is UnifiedConfig {
  return 'pictures' in config && Array.isArray(config.pictures);
}

function buildPromptFromUnified(picture: PictureConfig, style: string): string {
  // Combine style + topic + content into a single prompt
  return `${style}

---

请为以下内容生成一张信息图：

**主题方向**: ${picture.topic}

**内容**:
${picture.content}`;
}

function buildPromptFromLegacy(
  illustration: LegacyIllustration,
  style?: LegacyConfig['style']
): string {
  let prompt = '';

  if (style) {
    prompt += `Style: ${style.mode || 'light'} mode, `;
    prompt += `background ${style.background || '#F8F9FA'}, `;
    prompt += `primary color ${style.primary || '#2F2B42'}, `;
    if (style.accent) {
      prompt += `accent colors ${style.accent.join(', ')}. `;
    }
  }

  if (typeof illustration.prompt === 'string') {
    prompt += illustration.prompt;
  } else {
    prompt += JSON.stringify(illustration.prompt);
  }

  return prompt;
}

// Dimension maps for Qwen image generation
const ratioMap2K: Record<string, string> = {
  '1:1': '2048*2048',
  '2:3': '1365*2048',
  '3:2': '2048*1365',
  '3:4': '1536*2048',
  '4:3': '2048*1536',
  '4:5': '1638*2048',
  '5:4': '2048*1638',
  '9:16': '1152*2048',
  '16:9': '2688*1536',
  '21:9': '2688*1152',
  '2.35:1': '2688*1144'
};

const ratioMapDefault: Record<string, string> = {
  '1:1': '1024*1024',
  '2:3': '682*1024',
  '3:2': '1024*682',
  '3:4': '768*1024',
  '4:3': '1024*768',
  '4:5': '819*1024',
  '5:4': '1024*819',
  '9:16': '576*1024',
  '16:9': '1344*768',
  '21:9': '1344*576',
  '2.35:1': '1344*572'
};

async function generateImageOnce(
  prompt: string,
  model: string,
  apiKey: string,
  aspectRatio: string = '16:9',
  size: 'default' | '2k' = 'default'
): Promise<{ buffer: Buffer | null; status: number; retryable: boolean }> {
  const ratioMap = size === '2k' ? ratioMap2K : ratioMapDefault;
  const dimensions = ratioMap[aspectRatio] || ratioMap['16:9'];

  const requestBody = {
    model: model,
    input: {
      messages: [
        {
          role: 'user',
          content: [{ text: prompt }]
        }
      ]
    },
    parameters: {
      size: dimensions,
      n: 1,
      watermark: false,
      prompt_extend: true,
      negative_prompt: '低分辨率，低画质，肢体畸形，手指畸形，画面过饱和，蜡像感，人脸无细节，过度光滑，画面具有AI感。构图混乱。文字模糊，扭曲。'
    }
  };

  const response = await fetch(QWEN_API_BASE, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`
    },
    body: JSON.stringify(requestBody)
  });

  // 429 / 5xx → 可重试；其它非 2xx / 业务错误码 → 不重试
  const retryable = response.status === 429 || response.status >= 500;

  if (!response.ok) {
    let bodyText = '';
    try { bodyText = await response.text(); } catch { /* ignore */ }
    return { buffer: null, status: response.status, retryable };
  }

  const data: QwenResponse = await response.json();

  // Enhanced error handling
  if (data.code || (data.status_code && data.status_code !== 200)) {
    const errorMsg = data.message || `HTTP ${response.status}: ${response.statusText}`;
    const errorCode = data.code || data.status_code?.toString() || 'unknown';
    // 常见限流类业务码也视作可重试
    const codeStr = String(errorCode);
    const bizRetryable = codeStr === '429' || codeStr.includes('Throttling') || codeStr.includes('Rate');
    if (bizRetryable) {
      return { buffer: null, status: 429, retryable: true };
    }
    throw new Error(`Qwen API Error: ${errorMsg} (code: ${errorCode})`);
  }

  // Extract image URL from response
  const content = data.output?.choices?.[0]?.message?.content;
  if (Array.isArray(content)) {
    for (const part of content) {
      if (part.image) {
        // Download image from URL
        const imageUrl = part.image;
        const imageResponse = await fetch(imageUrl);
        const imageBuffer = Buffer.from(await imageResponse.arrayBuffer());
        return { buffer: imageBuffer, status: 200, retryable: false };
      }
    }
  }

  return { buffer: null, status: 200, retryable: false };
}

/**
 * 并发安全 + 限流重试的生图入口。
 * 遇到 429 / 5xx 按指数退避重试（1s → 2s → 4s ...），最多 maxRetries 次。
 */
const MAX_RETRIES = 4;
const INITIAL_BACKOFF_MS = 1000;

async function generateImage(
  prompt: string,
  model: string,
  apiKey: string,
  aspectRatio: string = '16:9',
  size: 'default' | '2k' = 'default'
): Promise<Buffer | null> {
  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    const result = await generateImageOnce(prompt, model, apiKey, aspectRatio, size);
    if (result.buffer !== null) {
      return result.buffer;
    }
    if (!result.retryable || attempt === MAX_RETRIES) {
      if (result.status !== 200) {
        throw new Error(`Qwen API Error: HTTP ${result.status}${result.retryable ? ' (rate-limited, retries exhausted)' : ''}`);
      }
      return null;
    }
    // 指数退避：1s → 2s → 4s → 8s，并加 ±20% 抖动避免并发群体同步重试
    const backoff = INITIAL_BACKOFF_MS * Math.pow(2, attempt);
    const jitter = backoff * (0.8 + Math.random() * 0.4);
    console.log(`  ⏳ 限流(HTTP ${result.status})，第 ${attempt + 1}/${MAX_RETRIES} 次重试，等待 ${(jitter / 1000).toFixed(1)}s...`);
    await sleep(Math.round(jitter));
  }
  return null;
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 简易 Promise 并发池：最多同时执行 concurrency 个任务，保持顺序无关。
 * 任务完成一个就立即启动下一个（非批次式），最大化吞吐。
 */
async function runWithConcurrency<T, R>(
  items: T[],
  concurrency: number,
  worker: (item: T, index: number) => Promise<R>
): Promise<R[]> {
  const results: R[] = new Array(items.length);
  let cursor = 0;

  async function runNext(): Promise<void> {
    while (true) {
      const idx = cursor++;
      if (idx >= items.length) return;
      results[idx] = await worker(items[idx], idx);
    }
  }

  const lanes = Math.min(concurrency, items.length);
  await Promise.all(Array.from({ length: lanes }, () => runNext()));
  return results;
}

function printUsage(): never {
  console.log(`
Batch Image Generation Script

Usage:
  npx -y bun batch-generate.ts --config slides.json --output-dir ./images

Options:
  -c, --config <path>       JSON config file (unified format, same as web version)
  -o, --output-dir <path>   Output directory (default: ./illustrations)
  -m, --model <model>       Model to use (default: qwen-image-2.0-pro)
  -s, --size <size>         Image size: 2k (2048px) or default (~1K, default)
  -d, --delay <ms>          Delay between requests in ms (serial mode only, default: 2000)
  -p, --prefix <text>       Filename prefix (default: from config filename)
  -r, --regenerate <ids>    Regenerate specific images (e.g., "3" or "3,5,7")
  -f, --force               Force regenerate all images (ignore existing)
      --concurrency <n>     Parallel image generation (default: 3). 1 = serial.
                            Increase only if your DashScope account has higher QPS.
  -h, --help                Show this help

Resume Generation:
  By default, the script skips images that already exist in the output directory.
  This allows you to resume interrupted generation without re-generating completed images.
  Use --force to regenerate all images, or --regenerate to regenerate specific ones.

Environment:
  DASHSCOPE_API_KEY         Required. Get from https://dashscope.console.aliyun.com/apiKey

Config File Format (Unified - same JSON as web version):
  {
    "instruction": "请为我绘制 7 张图片（generate 7 images）...",
    "batch_rules": {
      "total": 7,
      "one_item_one_image": true,
      "aspect_ratio": "16:9",
      "do_not_merge": true
    },
    "fallback": "如果无法一次生成全部图片...",
    "style": "完整的 style prompt（从 styles/style-light.md 复制）...",
    "pictures": [
      { "id": 1, "topic": "封面", "content": "Agent Skills 完全指南\\n\\n第1节：..." },
      { "id": 2, "topic": "核心概念", "content": "Skills 是什么..." }
    ]
  }

Output Filenames:
  {prefix}-{id:02d}.png  (e.g., SKILL_01-01.png, SKILL_01-02.png)
`);
  process.exit(0);
}

async function main() {
  const args = process.argv.slice(2);

  let configPath: string | null = null;
  let outputDir = './illustrations';
  let model = DEFAULT_MODEL;
  let size: 'default' | '2k' = 'default';
  let delay = 2000;
  let prefix: string | null = null;
  let forceRegenerate = false;
  let regenerateIds: Set<number> | null = null;
  let concurrency = 3;

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    switch (arg) {
      case '-h':
      case '--help':
        printUsage();
        break;
      case '-c':
      case '--config':
        configPath = args[++i];
        break;
      case '-o':
      case '--output-dir':
        outputDir = args[++i];
        break;
      case '-m':
      case '--model':
        model = args[++i];
        break;
      case '-s':
      case '--size':
        size = args[++i] as 'default' | '2k';
        break;
      case '-d':
      case '--delay':
        delay = parseInt(args[++i], 10);
        break;
      case '-p':
      case '--prefix':
        prefix = args[++i];
        break;
      case '-f':
      case '--force':
        forceRegenerate = true;
        break;
      case '-r':
      case '--regenerate':
        regenerateIds = new Set(
          args[++i].split(',').map(id => parseInt(id.trim(), 10))
        );
        break;
      case '--concurrency':
        concurrency = Math.max(1, parseInt(args[++i], 10) || 3);
        break;
    }
  }

  const apiKey = process.env.DASHSCOPE_API_KEY;
  if (!apiKey) {
    console.error('Error: DASHSCOPE_API_KEY environment variable is required');
    console.error('Get your API key from: https://dashscope.console.aliyun.com/apiKey');
    process.exit(1);
  }

  if (!configPath) {
    console.error('Error: --config is required');
    process.exit(1);
  }

  const configContent = await readFile(configPath, 'utf-8');
  const config: BatchConfig = JSON.parse(configContent);

  // Auto-detect prefix from config filename if not specified
  if (!prefix) {
    prefix = basename(configPath, '.json').replace(/-slides$/, '');
  }

  await mkdir(outputDir, { recursive: true });

  // Handle unified format vs legacy format
  if (isUnifiedConfig(config)) {
    // Unified format (new)
    const total = config.pictures.length;
    let success = 0;
    let failed = 0;
    let skipped = 0;

    console.log(`\nBatch Image Generation (Unified Format)`);
    console.log(`=======================================`);
    console.log(`Model: ${model}`);
    console.log(`Size: ${size}`);
    console.log(`Total: ${total} images`);
    console.log(`Prefix: ${prefix}`);
    console.log(`Output: ${outputDir}`);
    if (concurrency > 1) {
      console.log(`Concurrency: ${concurrency} (parallel)`);
    } else {
      console.log(`Delay: ${delay}ms between requests (serial mode)`);
    }
    if (forceRegenerate) {
      console.log(`Mode: Force regenerate all`);
    } else if (regenerateIds) {
      console.log(`Mode: Regenerate specific IDs: ${[...regenerateIds].join(', ')}`);
    } else {
      console.log(`Mode: Resume (skip existing)`);
    }
    console.log();

    // 先过滤出需要生成的项（跳过已存在）
    const todo: { picture: PictureConfig; filename: string; outputPath: string }[] = [];
    for (const picture of config.pictures) {
      const filename = `${prefix}-${String(picture.id).padStart(2, '0')}.png`;
      const outputPath = join(outputDir, filename);

      const fileExists = existsSync(outputPath);
      const shouldRegenerate = regenerateIds?.has(picture.id);
      const shouldSkip = fileExists && !forceRegenerate && !shouldRegenerate;

      if (shouldSkip) {
        console.log(`[${picture.id}/${total}] Skipping: ${filename} (already exists)`);
        skipped++;
      } else {
        todo.push({ picture, filename, outputPath });
      }
    }

    if (todo.length > 0) {
      if (concurrency > 1) {
        console.log(`Generating ${todo.length} image(s) in parallel (concurrency=${concurrency})...\n`);
      }
      const startTime = Date.now();
      let completed = 0;

      await runWithConcurrency(todo, concurrency, async (task) => {
        const { picture, filename, outputPath } = task;
        const shouldRegenerate = regenerateIds?.has(picture.id);

        // 串行模式：除第一张外，每张前 sleep
        if (concurrency === 1 && completed > 0) {
          console.log(`  Waiting ${delay}ms...`);
          await sleep(delay);
        }

        console.log(`[${picture.id}/${total}] Generating: ${filename}`);
        console.log(`  Topic: ${picture.topic}`);
        if (shouldRegenerate) {
          console.log(`  (Regenerating as requested)`);
        }

        try {
          const prompt = buildPromptFromUnified(picture, config.style);
          const imageBuffer = await generateImage(prompt, model, apiKey, config.batch_rules?.aspect_ratio || '16:9', size);

          completed++;
          if (imageBuffer) {
            await mkdir(dirname(outputPath), { recursive: true });
            await writeFile(outputPath, imageBuffer);
            console.log(`  ✓ Saved (${(imageBuffer.length / 1024).toFixed(1)} KB) [${completed}/${todo.length}]`);
            success++;
          } else {
            console.log(`  ✗ No image generated [${completed}/${todo.length}]`);
            failed++;
          }
        } catch (error) {
          completed++;
          console.log(`  ✗ Error: ${error instanceof Error ? error.message : error} [${completed}/${todo.length}]`);
          failed++;
        }
      });

      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      console.log(`\nElapsed: ${elapsed}s (avg ${(parseFloat(elapsed) / todo.length).toFixed(1)}s/image)`);
    }

    console.log(`\n=======================================`);
    if (skipped > 0) {
      console.log(`Complete: ${success} generated, ${skipped} skipped, ${failed} failed`);
    } else {
      console.log(`Complete: ${success}/${total} succeeded, ${failed} failed`);
    }
    console.log(`Output directory: ${outputDir}`);

  } else {
    // Legacy format (backward compatibility)
    const legacyConfig = config as LegacyConfig;

    if (!legacyConfig.illustrations || legacyConfig.illustrations.length === 0) {
      console.error('Error: No illustrations in config');
      process.exit(1);
    }

    const total = legacyConfig.illustrations.length;
    let success = 0;
    let failed = 0;
    let skipped = 0;

    console.log(`\nBatch Image Generation (Legacy Format)`);
    console.log(`======================================`);
    console.log(`Model: ${model}`);
    console.log(`Size: ${size}`);
    console.log(`Total: ${total} images`);
    console.log(`Output: ${outputDir}`);
    if (concurrency > 1) {
      console.log(`Concurrency: ${concurrency} (parallel)`);
    } else {
      console.log(`Delay: ${delay}ms between requests (serial mode)`);
    }
    if (forceRegenerate) {
      console.log(`Mode: Force regenerate all`);
    } else if (regenerateIds) {
      console.log(`Mode: Regenerate specific IDs: ${[...regenerateIds].join(', ')}`);
    } else {
      console.log(`Mode: Resume (skip existing)`);
    }
    console.log();

    // 先过滤出需要生成的项（跳过已存在）
    const legacyTodo: { illustration: LegacyIllustration; outputPath: string }[] = [];
    for (const illustration of legacyConfig.illustrations) {
      const outputPath = join(outputDir, illustration.filename);
      const fileExists = existsSync(outputPath);
      const shouldRegenerate = regenerateIds?.has(illustration.id);
      const shouldSkip = fileExists && !forceRegenerate && !shouldRegenerate;

      if (shouldSkip) {
        console.log(`[${illustration.id}/${total}] Skipping: ${illustration.filename} (already exists)`);
        skipped++;
      } else {
        legacyTodo.push({ illustration, outputPath });
      }
    }

    if (legacyTodo.length > 0) {
      if (concurrency > 1) {
        console.log(`Generating ${legacyTodo.length} image(s) in parallel (concurrency=${concurrency})...\n`);
      }
      const startTime = Date.now();
      let completed = 0;

      await runWithConcurrency(legacyTodo, concurrency, async (task) => {
        const { illustration, outputPath } = task;
        const shouldRegenerate = regenerateIds?.has(illustration.id);

        if (concurrency === 1 && completed > 0) {
          await sleep(delay);
        }

        console.log(`[${illustration.id}/${total}] Generating: ${illustration.filename}`);
        if (shouldRegenerate) {
          console.log(`  (Regenerating as requested)`);
        }

        try {
          const prompt = buildPromptFromLegacy(illustration, legacyConfig.style);
          const imageBuffer = await generateImage(prompt, model, apiKey, '16:9', size);

          completed++;
          if (imageBuffer) {
            await mkdir(dirname(outputPath), { recursive: true });
            await writeFile(outputPath, imageBuffer);
            console.log(`  ✓ Saved (${(imageBuffer.length / 1024).toFixed(1)} KB) [${completed}/${legacyTodo.length}]`);
            success++;
          } else {
            console.log(`  ✗ No image generated [${completed}/${legacyTodo.length}]`);
            failed++;
          }
        } catch (error) {
          completed++;
          console.log(`  ✗ Error: ${error instanceof Error ? error.message : error} [${completed}/${legacyTodo.length}]`);
          failed++;
        }
      });

      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      console.log(`\nElapsed: ${elapsed}s (avg ${(parseFloat(elapsed) / legacyTodo.length).toFixed(1)}s/image)`);
    }

    console.log(`\n======================================`);
    if (skipped > 0) {
      console.log(`Complete: ${success} generated, ${skipped} skipped, ${failed} failed`);
    } else {
      console.log(`Complete: ${success}/${total} succeeded, ${failed} failed`);
    }
    console.log(`Output directory: ${outputDir}`);
  }
}

main();
