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

async function generateImage(
  prompt: string,
  model: string,
  apiKey: string,
  aspectRatio: string = '16:9',
  size: 'default' | '2k' = 'default'
): Promise<Buffer | null> {
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

  const data: QwenResponse = await response.json();

  // Enhanced error handling
  if (!response.ok || data.code || (data.status_code && data.status_code !== 200)) {
    const errorMsg = data.message || `HTTP ${response.status}: ${response.statusText}`;
    const errorCode = data.code || data.status_code?.toString() || 'unknown';
    throw new Error(`Qwen API Error: ${errorMsg} (code: ${errorCode})`);
  }

  // Extract image URL from response
  const content = data.output?.choices?.[0]?.message?.content;
  if (Array.isArray(content)) {
    for (const part of content) {
      if (part.image) {
        // Download image from URL
        const imageUrl = part.image;
        console.log(`  Downloading image from Qwen...`);

        const imageResponse = await fetch(imageUrl);
        const imageBuffer = Buffer.from(await imageResponse.arrayBuffer());
        return imageBuffer;
      }
    }
  }

  return null;
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
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
  -d, --delay <ms>          Delay between requests in ms (default: 2000)
  -p, --prefix <text>       Filename prefix (default: from config filename)
  -r, --regenerate <ids>    Regenerate specific images (e.g., "3" or "3,5,7")
  -f, --force               Force regenerate all images (ignore existing)
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
    console.log(`Delay: ${delay}ms between requests`);
    if (forceRegenerate) {
      console.log(`Mode: Force regenerate all`);
    } else if (regenerateIds) {
      console.log(`Mode: Regenerate specific IDs: ${[...regenerateIds].join(', ')}`);
    } else {
      console.log(`Mode: Resume (skip existing)`);
    }
    console.log();

    let needsDelay = false;

    for (const picture of config.pictures) {
      const filename = `${prefix}-${String(picture.id).padStart(2, '0')}.png`;
      const outputPath = join(outputDir, filename);

      // Check if we should skip this image
      const fileExists = existsSync(outputPath);
      const shouldRegenerate = regenerateIds?.has(picture.id);
      const shouldSkip = fileExists && !forceRegenerate && !shouldRegenerate;

      if (shouldSkip) {
        console.log(`[${picture.id}/${total}] Skipping: ${filename} (already exists)`);
        skipped++;
        continue;
      }

      // Add delay before generation (except for first image)
      if (needsDelay) {
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

        if (imageBuffer) {
          await mkdir(dirname(outputPath), { recursive: true });
          await writeFile(outputPath, imageBuffer);
          console.log(`  ✓ Saved (${(imageBuffer.length / 1024).toFixed(1)} KB)`);
          success++;
          needsDelay = true;
        } else {
          console.log(`  ✗ No image generated`);
          failed++;
          needsDelay = true;
        }
      } catch (error) {
        console.log(`  ✗ Error: ${error instanceof Error ? error.message : error}`);
        failed++;
        needsDelay = true;
      }
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
    if (forceRegenerate) {
      console.log(`Mode: Force regenerate all`);
    } else if (regenerateIds) {
      console.log(`Mode: Regenerate specific IDs: ${[...regenerateIds].join(', ')}`);
    } else {
      console.log(`Mode: Resume (skip existing)`);
    }
    console.log();

    let needsDelay = false;

    for (const illustration of legacyConfig.illustrations) {
      const outputPath = join(outputDir, illustration.filename);

      // Check if we should skip this image
      const fileExists = existsSync(outputPath);
      const shouldRegenerate = regenerateIds?.has(illustration.id);
      const shouldSkip = fileExists && !forceRegenerate && !shouldRegenerate;

      if (shouldSkip) {
        console.log(`[${illustration.id}/${total}] Skipping: ${illustration.filename} (already exists)`);
        skipped++;
        continue;
      }

      // Add delay before generation (except for first image)
      if (needsDelay) {
        await sleep(delay);
      }

      console.log(`[${illustration.id}/${total}] Generating: ${illustration.filename}`);
      if (shouldRegenerate) {
        console.log(`  (Regenerating as requested)`);
      }

      try {
        const prompt = buildPromptFromLegacy(illustration, legacyConfig.style);
        const imageBuffer = await generateImage(prompt, model, apiKey, '16:9', size);

        if (imageBuffer) {
          await mkdir(dirname(outputPath), { recursive: true });
          await writeFile(outputPath, imageBuffer);
          console.log(`  ✓ Saved (${(imageBuffer.length / 1024).toFixed(1)} KB)`);
          success++;
          needsDelay = true;
        } else {
          console.log(`  ✗ No image generated`);
          failed++;
          needsDelay = true;
        }
      } catch (error) {
        console.log(`  ✗ Error: ${error instanceof Error ? error.message : error}`);
        failed++;
        needsDelay = true;
      }
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
