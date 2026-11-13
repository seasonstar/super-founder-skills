/**
 * Upload Markdown images to CSDN's own image host before saveArticle.
 *
 * External URLs such as wmimg.com are dropped when CSDN tries to mirror them.
 * Images already on *.csdnimg.cn or *.csdn.net are left unchanged.
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const BIZ_API = 'https://bizapi.csdn.net';
const SIGNATURE_PATH = '/resource-api/v1/image/direct/upload/signature';
const CA_KEY = '203803574';
const CA_SECRET = '9znpamsyl2c7cdrr9sas0le9vbc3r6ba';
const CACHE_FILE = path.join(__dirname, '../config/csdn_image_cache.json');
const MAX_IMAGE_BYTES = 10 * 1024 * 1024;
const MARKDOWN_IMAGE = /!\[([^\]]*)\]\(\s*<?([^)\s>]+)>?(?:\s+"[^"]*")?\s*\)/g;
const HTML_IMAGE = /(<img\b[^>]*\bsrc=["'])([^"']+)(["'][^>]*>)/gi;

const MIME_BY_SUFFIX = {
  jpg: 'image/jpeg',
  jpeg: 'image/jpeg',
  png: 'image/png',
  gif: 'image/gif',
  webp: 'image/webp',
  bmp: 'image/bmp'
};

function loadCache() {
  if (!fs.existsSync(CACHE_FILE)) {
    return {};
  }
  try {
    return JSON.parse(fs.readFileSync(CACHE_FILE, 'utf-8'));
  } catch {
    return {};
  }
}

function saveCache(cache) {
  fs.writeFileSync(CACHE_FILE, `${JSON.stringify(cache, null, 2)}\n`, 'utf-8');
}

function isRemote(src) {
  return /^https?:\/\//i.test(src);
}

function isCsdnHosted(src) {
  if (!isRemote(src)) {
    return false;
  }
  try {
    const host = new URL(src).hostname.toLowerCase();
    return host === 'csdnimg.cn' || host.endsWith('.csdnimg.cn') || host.endsWith('.csdn.net');
  } catch {
    return false;
  }
}

function suffixOf(name) {
  const clean = String(name || '').split('?')[0].split('#')[0];
  const ext = path.extname(clean).slice(1).toLowerCase();
  if (ext === 'jpeg') {
    return 'jpg';
  }
  return MIME_BY_SUFFIX[ext] ? ext : 'png';
}

function collectSources(markdown) {
  const sources = [];
  const seen = new Set();

  function add(src) {
    const value = String(src || '').trim();
    if (!value || value.startsWith('data:') || seen.has(value)) {
      return;
    }
    seen.add(value);
    sources.push(value);
  }

  for (const match of markdown.matchAll(MARKDOWN_IMAGE)) {
    add(match[2]);
  }
  for (const match of markdown.matchAll(HTML_IMAGE)) {
    add(match[2]);
  }
  return sources;
}

function resolveLocalPath(src, baseDir) {
  if (path.isAbsolute(src)) {
    return src;
  }
  const fromArticle = path.resolve(baseDir, src);
  if (fs.existsSync(fromArticle)) {
    return fromArticle;
  }
  return path.resolve(process.cwd(), src);
}

async function readImage(src, baseDir) {
  if (isRemote(src)) {
    const response = await fetch(src, {
      redirect: 'follow',
      headers: {
        'user-agent': 'Mozilla/5.0',
        accept: 'image/*,*/*'
      }
    });
    if (!response.ok) {
      throw new Error(`下载图片失败 ${response.status}: ${src}`);
    }
    const bytes = Buffer.from(await response.arrayBuffer());
    if (bytes.length > MAX_IMAGE_BYTES) {
      throw new Error(`图片超过 10MB: ${src}`);
    }
    const name = path.basename(new URL(src).pathname) || 'image.png';
    return { bytes, name };
  }

  const filePath = resolveLocalPath(src, baseDir);
  if (!fs.existsSync(filePath)) {
    throw new Error(`本地图片不存在: ${src}`);
  }
  const bytes = fs.readFileSync(filePath);
  if (bytes.length > MAX_IMAGE_BYTES) {
    throw new Error(`图片超过 10MB: ${filePath}`);
  }
  return { bytes, name: path.basename(filePath) };
}

function signBizApi(method, apiPath) {
  const nonce = crypto.randomUUID();
  const contentType = 'application/json';
  const stringToSign = [
    method,
    '*/*',
    '',
    contentType,
    '',
    `x-ca-key:${CA_KEY}`,
    `x-ca-nonce:${nonce}`,
    apiPath
  ].join('\n');
  const signature = crypto.createHmac('sha256', CA_SECRET).update(stringToSign).digest('base64');
  return {
    accept: '*/*',
    'content-type': contentType,
    'x-ca-key': CA_KEY,
    'x-ca-nonce': nonce,
    'x-ca-signature': signature,
    'x-ca-signature-headers': 'x-ca-key,x-ca-nonce'
  };
}

function buildMultipart(fields, file) {
  const boundary = `----csdn${crypto.randomBytes(12).toString('hex')}`;
  const chunks = [];
  for (const [name, value] of Object.entries(fields)) {
    chunks.push(Buffer.from(
      `--${boundary}\r\nContent-Disposition: form-data; name="${name}"\r\n\r\n${value}\r\n`
    ));
  }
  chunks.push(Buffer.from(
    `--${boundary}\r\nContent-Disposition: form-data; name="file"; filename="${file.filename}"\r\nContent-Type: ${file.type}\r\n\r\n`
  ));
  chunks.push(file.bytes);
  chunks.push(Buffer.from(`\r\n--${boundary}--\r\n`));
  return { body: Buffer.concat(chunks), boundary };
}

async function uploadBytes(bytes, filename, cookie) {
  const suffix = suffixOf(filename);
  const signHeaders = signBizApi('POST', SIGNATURE_PATH);
  const credentialResponse = await fetch(`${BIZ_API}${SIGNATURE_PATH}`, {
    method: 'POST',
    headers: {
      ...signHeaders,
      cookie,
      origin: 'https://editor.csdn.net',
      referer: 'https://editor.csdn.net/',
      'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    },
    body: JSON.stringify({
      imageTemplate: '',
      appName: 'direct_blog_markdown',
      imageSuffix: suffix
    })
  });
  const credentialText = await credentialResponse.text();
  let credential;
  try {
    credential = JSON.parse(credentialText);
  } catch {
    throw new Error(`获取 CSDN 上传凭证失败，响应不是 JSON（HTTP ${credentialResponse.status}）`);
  }
  const ticket = credential.data || {};
  if (credential.code !== 200 || !ticket.policy || !ticket.accessId || !ticket.signature || !ticket.filePath || !ticket.host) {
    const message = credential.message || credential.msg || `HTTP ${credentialResponse.status}`;
    throw new Error(`获取 CSDN 上传凭证失败: ${message}`);
  }

  const custom = ticket.customParam || {};
  const { body, boundary } = buildMultipart({
    key: ticket.filePath,
    policy: ticket.policy,
    signature: ticket.signature,
    callbackBody: ticket.callbackBody || '',
    callbackBodyType: ticket.callbackBodyType || '',
    callbackUrl: ticket.callbackUrl || '',
    AccessKeyId: ticket.accessId,
    'x:rtype': custom.rtype || '',
    'x:filePath': custom.filePath || '',
    'x:isAudit': String(custom.isAudit ?? 0),
    'x:x-image-app': custom['x-image-app'] || '',
    'x:type': custom.type || '',
    'x:x-image-suffix': custom['x-image-suffix'] || '',
    'x:username': custom.username || ''
  }, {
    filename: `image.${suffix}`,
    type: MIME_BY_SUFFIX[suffix],
    bytes
  });

  const uploadResponse = await fetch(ticket.host, {
    method: 'POST',
    headers: {
      accept: 'application/json, text/javascript, */*; q=0.01',
      'content-type': `multipart/form-data; boundary=${boundary}`,
      origin: 'https://editor.csdn.net',
      referer: 'https://editor.csdn.net/',
      'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    },
    body
  });
  const uploadText = await uploadResponse.text();
  let uploaded;
  try {
    uploaded = JSON.parse(uploadText);
  } catch {
    throw new Error(`CSDN 图床返回的不是 JSON（HTTP ${uploadResponse.status}）: ${uploadText.slice(0, 180)}`);
  }
  const imageUrl = uploaded.data && uploaded.data.imageUrl;
  if (uploaded.code !== 200 || !isCsdnHosted(imageUrl)) {
    const message = uploaded.message || uploaded.msg || uploaded.code || `HTTP ${uploadResponse.status}`;
    throw new Error(`上传到 CSDN 图床失败: ${message}`);
  }
  return imageUrl;
}

/**
 * Replace local and third-party images in Markdown with CSDN-hosted URLs.
 *
 * @param {string} markdown
 * @param {{ baseDir?: string, cookie: string, onProgress?: (message: string) => void }} options
 * @returns {Promise<{ markdown: string, uploaded: number, reused: number, skipped: number }>}
 */
async function rehostMarkdownImages(markdown, options) {
  const baseDir = options.baseDir || process.cwd();
  const onProgress = options.onProgress || (() => {});
  const sources = collectSources(markdown);
  const pending = sources.filter((src) => !isCsdnHosted(src));
  const skipped = sources.length - pending.length;

  if (pending.length === 0) {
    return { markdown, uploaded: 0, reused: 0, skipped };
  }
  if (!options.cookie) {
    throw new Error('上传图片需要配置 headers.Cookie');
  }

  const cache = loadCache();
  const replacements = new Map();
  let uploaded = 0;
  let reused = 0;

  for (const src of pending) {
    const image = await readImage(src, baseDir);
    const hash = crypto.createHash('sha256').update(image.bytes).digest('hex');
    let target = cache[hash];
    if (target && isCsdnHosted(target)) {
      reused += 1;
      onProgress(`复用已上传图片: ${image.name}`);
    } else {
      onProgress(`上传到 CSDN 图床: ${image.name}`);
      target = await uploadBytes(image.bytes, image.name, options.cookie);
      cache[hash] = target;
      saveCache(cache);
      uploaded += 1;
      onProgress(`  -> ${target}`);
    }
    replacements.set(src, target);
  }

  let next = markdown;
  for (const [from, to] of replacements) {
    next = next.split(from).join(to);
  }
  return { markdown: next, uploaded, reused, skipped };
}

module.exports = {
  rehostMarkdownImages,
  isCsdnHosted
};
