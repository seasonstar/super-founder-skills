#!/usr/bin/env bun
/**
 * Image Generation Script (Qwen / 千问文生图)
 *
 * Supports:
 * - Qwen Image 2.0 Pro (default, for users in China)
 *
 * Generate images using Qwen text-to-image API
 */

import { parseArgs } from 'node:util';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { dirname, extname, resolve, isAbsolute } from 'node:path';
import { homedir } from 'node:os';

// Types
interface ReferenceImage {
  mimeType: string;
  base64: string;
}

interface Config {
  references?: string[];
  model?: string;
  size?: 'default' | '2k';
  aspectRatio?: string;
}

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

// Default models
const DEFAULT_QWEN_MODEL = 'qwen-image-2.0-pro';

// Supported aspect ratios for Qwen
type AspectRatio = '1:1' | '2:3' | '3:2' | '3:4' | '4:3' | '4:5' | '5:4' | '9:16' | '16:9' | '21:9' | '2.35:1';

// Dimension maps
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

/**
 * Get dimensions based on aspect ratio and size
 */
function getDimensions(size: 'default' | '2k', aspectRatio?: AspectRatio): string {
  if (aspectRatio) {
    return size === '2k'
      ? (ratioMap2K[aspectRatio] || '2688*1536')
      : (ratioMapDefault[aspectRatio] || '1344*768');
  }
  return size === '2k' ? '2688*1536' : '1344*768';
}

/**
 * Generate image using Qwen (通义千问) API
 */
async function generateImageQwen(
  prompt: string,
  model: string,
  apiKey: string,
  size: 'default' | '2k',
  aspectRatio?: AspectRatio
): Promise<{ imageData: Buffer; mimeType: string } | null> {
  const dimensions = getDimensions(size, aspectRatio);

  // Build request body for Qwen
  const messages = [
    {
      role: 'user',
      content: [{ text: prompt }]
    }
  ];

  const requestBody = {
    model: model,
    input: {
    messages: messages
  },
    parameters: {
    size: dimensions,
    n: 1,
    watermark: false,
    prompt_extend: true,
    negative_prompt: '低分辨率，低画质，肢体畸形，手指畸形，画面过饱和，蜡像感，人脸无细节，过度光滑，画面具有AI感。构图混乱。文字模糊，扭曲。'
  }
  };

  const url = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation';

  const response = await fetch(url, {
    method: 'POST',
    headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${apiKey}`
  },
    body: JSON.stringify(requestBody)
  });

  const data: QwenResponse = await response.json();

  // Enhanced error handling: check both HTTP status and response body
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
        console.log(`Downloading image from: ${imageUrl}`);

        const imageResponse = await fetch(imageUrl);
        const imageBuffer = Buffer.from(await imageResponse.arrayBuffer());

        return {
          imageData: imageBuffer,
          mimeType: 'image/png'
        };
      }
    }
  }

  return null;
}

/**
 * Load reference images (note: Qwen doesn't support reference images)
 */
async function loadReferenceImages(paths: string[]): Promise<ReferenceImage[]> {
  console.log('Warning: Qwen does not support reference images. They will be ignored.');
  return [];
}

function printUsage(): never {
  console.log(`
Image Generation Script (Qwen / 千问文生图)

Usage:
  npx -y bun generate-image.ts --prompt "description" --output image.png
  npx -y bun generate-image.ts --prompt-file prompt.md --output image.png

Options:
  -p, --prompt <text>       Image description
  -f, --prompt-file <path>  Read prompt from file
  -o, --output <path>       Output image path (default: generated.png)
  -m, --model <model>       Model to use (default: qwen-image-2.0-pro)
  --size <size>             Image size: 2k (2048px, default) or default (~1.4K)
  -a, --aspect-ratio <ratio>  Aspect ratio: 1:1, 3:4, 4:3, 9:16, 16:9, 21:9, etc.
  -h, --help                Show this help

Style Configuration (persistent settings):
  --save-config             Save current settings to project config (.smart-illustrator/config.json)
  --save-config-global      Save current settings to user config (~/.smart-illustrator/config.json)
  --no-config               Ignore config files, use only command-line arguments

Environment Variables:
  DASHSCOPE_API_KEY         Qwen API key (required)

Examples:
  # Using Qwen API
  DASHSCOPE_API_KEY=xxx npx -y bun generate-image.ts -p "A futuristic city" -o city.png

  # From prompt file
  DASHSCOPE_API_KEY=xxx npx -y bun generate-image.ts -f illustration-prompt.md -o illustration.png

Note: This script uses Qwen (通义千问) for image generation,`);
  process.exit(0);
}

async function main() {
  const args = process.argv.slice(2);

  let prompt: string | null = null;
  let promptFile: string | null = null;
  let output = 'generated.png';
  let model: string | null = null;
  let size: 'default' | '2k' = '2k';  // Default to 2K resolution
  let aspectRatio: AspectRatio | undefined;
  let shouldSaveConfig = false;
  let saveConfigGlobal = false;
  let noConfig = false;

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    switch (arg) {
      case '-h':
      case '--help':
        printUsage();
        break;
      case '-p':
      case '--prompt':
        prompt = args[++i];
        break;
      case '-f':
      case '--prompt-file':
        promptFile = args[++i];
        break;
      case '-o':
      case '--output':
        output = args[++i];
        break;
      case '-m':
      case '--model':
        model = args[++i];
        break;
      case '--size':
        size = args[++i] as 'default' | '2k';
        break;
      case '-a':
      case '--aspect-ratio':
        aspectRatio = args[++i] as AspectRatio;
        break;
      case '--save-config':
        shouldSaveConfig = true;
        break;
      case '--save-config-global':
        saveConfigGlobal = true;
        break;
      case '--no-config':
        noConfig = true;
        break;
    }
  }

  // Get API key
  const apiKey = process.env.DASHSCOPE_API_KEY;

  if (!apiKey) {
    console.error('Error: DASHSCOPE_API_KEY environment variable is required');
    console.error('Please set it: export DASHSCOPE_API_KEY="your-api-key"');
    process.exit(1);
  }

  // Set default model
  if (!model) {
    model = DEFAULT_QWEN_MODEL;
  }

  if (promptFile) {
    prompt = await readFile(promptFile, 'utf-8');
  }

  if (!prompt) {
    console.error('Error: --prompt or --prompt-file is required');
    process.exit(1);
  }

  console.log(`Model: ${model}`);
  console.log(`Size: ${size}`);
  if (aspectRatio) {
    console.log(`Aspect ratio: ${aspectRatio}`);
  }

  // Calculate dimensions for logging
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
  const dimensions = getDimensions(size, aspectRatio);

  console.log(`Prompt: ${prompt.slice(0, 100)}${prompt.length > 100 ? '...' : ''}`);

  try {
    // Ensure output directory exists
    await mkdir(dirname(output), { recursive: true });

    console.log('\nGenerating image...');

    const result = await generateImageQwen(prompt, model!, apiKey, size, aspectRatio);

    if (!result) {
      console.error('Error: No image generated');
      process.exit(1);
    }

    // Save image
    await writeFile(output, result.imageData);

    const fileSizeKB = (result.imageData.length / 1024).toFixed(1);
    console.log(`\n✅ Image saved to: ${output}`);
    console.log(`   File size: ${fileSizeKB} KB`);
    console.log(`   Dimensions: ${dimensions}`);

  } catch (error) {
    console.error('\n❌ Error:', error instanceof Error ? error.message : error);
    process.exit(1);
  }
}

main();
