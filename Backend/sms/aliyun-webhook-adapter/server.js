'use strict';

const crypto = require('crypto');
const http = require('http');

const MAX_BODY_BYTES = 16 * 1024;
const DEFAULT_HOST = '127.0.0.1';
const DEFAULT_PORT = 8791;
const DEFAULT_ENDPOINT = 'https://dysmsapi.aliyuncs.com';
const DEFAULT_API_VERSION = '2017-05-25';
const DEFAULT_REGION_ID = 'cn-hangzhou';

let aliyunClient = null;

function jsonResponse(res, status, body) {
  const payload = Buffer.from(JSON.stringify(body), 'utf8');
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': payload.length,
    'Cache-Control': 'no-store',
  });
  res.end(payload);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let size = 0;
    req.on('data', (chunk) => {
      size += chunk.length;
      if (size > MAX_BODY_BYTES) {
        reject(Object.assign(new Error('body too large'), { statusCode: 413 }));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on('end', () => resolve(Buffer.concat(chunks)));
    req.on('error', reject);
  });
}

function expectedSignature(secret, payload) {
  return crypto.createHmac('sha256', secret).update(payload).digest('hex');
}

function timingSafeEqualHex(left, right) {
  const supplied = String(right || '').trim().toLowerCase();
  if (!/^[a-f0-9]{64}$/.test(supplied)) {
    return false;
  }
  const expectedBuffer = Buffer.from(left, 'hex');
  const suppliedBuffer = Buffer.from(supplied, 'hex');
  return suppliedBuffer.length === expectedBuffer.length && crypto.timingSafeEqual(expectedBuffer, suppliedBuffer);
}

function verifyWebhookSignature(secret, payload, suppliedSignature) {
  if (!secret) {
    return false;
  }
  return timingSafeEqualHex(expectedSignature(secret, payload), suppliedSignature);
}

function normalizeAliyunPhoneNumber(phoneNumber) {
  const value = String(phoneNumber || '').trim();
  const mainland = value.match(/^\+86(1[3-9]\d{9})$/);
  if (mainland) {
    return mainland[1];
  }
  if (/^1[3-9]\d{9}$/.test(value)) {
    return value;
  }
  if (/^\+[1-9]\d{7,15}$/.test(value)) {
    return value.slice(1);
  }
  return null;
}

function maskedPhone(phoneNumber) {
  const value = String(phoneNumber || '');
  return value.length <= 4 ? '****' : `****${value.slice(-4)}`;
}

function requiredEnv(name) {
  const value = String(process.env[name] || '').trim();
  if (!value) {
    throw Object.assign(new Error(`missing ${name}`), { statusCode: 503, publicCode: 'sms_provider_missing' });
  }
  return value;
}

function getAliyunClient() {
  if (aliyunClient) {
    return aliyunClient;
  }
  const Core = require('@alicloud/pop-core');
  aliyunClient = new Core({
    accessKeyId: requiredEnv('ALIYUN_ACCESS_KEY_ID'),
    accessKeySecret: requiredEnv('ALIYUN_ACCESS_KEY_SECRET'),
    endpoint: process.env.ALIYUN_SMS_ENDPOINT || DEFAULT_ENDPOINT,
    apiVersion: DEFAULT_API_VERSION,
  });
  return aliyunClient;
}

async function sendAliyunSms(payload) {
  const phoneNumber = normalizeAliyunPhoneNumber(payload.phoneNumber);
  const code = String(payload.code || '').trim();
  const templateCode = String(payload.templateId || process.env.ALIYUN_TEMPLATE_CODE || '').trim();

  if (!phoneNumber || !/^\d{6}$/.test(code)) {
    throw Object.assign(new Error('invalid payload'), { statusCode: 400, publicCode: 'invalid_sms_payload' });
  }
  if (!templateCode) {
    throw Object.assign(new Error('missing template code'), { statusCode: 503, publicCode: 'sms_provider_missing' });
  }

  if (process.env.XNP_SMS_ADAPTER_MOCK === '1' || process.env.SMS_MOCK === '1') {
    return { Code: 'OK', Message: 'mock', Mock: true };
  }

  const client = getAliyunClient();
  const params = {
    RegionId: process.env.ALIYUN_REGION_ID || DEFAULT_REGION_ID,
    PhoneNumbers: phoneNumber,
    SignName: requiredEnv('ALIYUN_SIGN_NAME'),
    TemplateCode: templateCode,
    TemplateParam: JSON.stringify({ code }),
  };

  const result = await client.request('SendSms', params, { method: 'POST' });
  if (!result || result.Code !== 'OK') {
    const codeValue = result && result.Code ? result.Code : 'Unknown';
    const statusCode = codeValue === 'isv.BUSINESS_LIMIT_CONTROL' ? 429 : 502;
    throw Object.assign(new Error(`aliyun send failed: ${codeValue}`), {
      statusCode,
      publicCode: 'sms_provider_failed',
      aliyunCode: codeValue,
      aliyunMessage: result && result.Message ? result.Message : '',
    });
  }
  return result;
}

async function handleSend(req, res) {
  const secret = process.env.XNP_SMS_SECRET || process.env.XNP_SMS_WEBHOOK_SECRET || '';
  const body = await readBody(req);
  if (!verifyWebhookSignature(secret, body, req.headers['x-xnp-signature'])) {
    jsonResponse(res, 401, { error: { code: 'invalid_signature', message: 'webhook signature invalid' } });
    return;
  }

  let payload;
  try {
    payload = JSON.parse(body.toString('utf8'));
  } catch (_error) {
    jsonResponse(res, 400, { error: { code: 'invalid_json', message: 'request body must be JSON' } });
    return;
  }

  try {
    const result = await sendAliyunSms(payload);
    jsonResponse(res, 200, {
      sent: true,
      provider: result.Mock ? 'aliyun_mock' : 'aliyun_dysmsapi',
      requestId: result.RequestId || null,
    });
  } catch (error) {
    console.error(JSON.stringify({
      event: 'sms_send_failed',
      code: error.publicCode || 'sms_provider_failed',
      aliyunCode: error.aliyunCode || null,
      phone: maskedPhone(payload && payload.phoneNumber),
    }));
    jsonResponse(res, error.statusCode || 502, {
      error: {
        code: error.publicCode || 'sms_provider_failed',
        message: 'sms provider failed',
      },
    });
  }
}

function createServer() {
  return http.createServer(async (req, res) => {
    try {
      if (req.method === 'GET' && req.url === '/healthz') {
        jsonResponse(res, 200, {
          status: 'ok',
          provider: process.env.XNP_SMS_ADAPTER_MOCK === '1' || process.env.SMS_MOCK === '1' ? 'aliyun_mock' : 'aliyun_dysmsapi',
        });
        return;
      }
      if (req.method === 'POST' && req.url === '/send') {
        await handleSend(req, res);
        return;
      }
      jsonResponse(res, 404, { error: { code: 'not_found', message: 'not found' } });
    } catch (error) {
      jsonResponse(res, error.statusCode || 500, {
        error: {
          code: error.statusCode === 413 ? 'body_too_large' : 'internal_error',
          message: 'request failed',
        },
      });
    }
  });
}

if (require.main === module) {
  const host = process.env.XNP_SMS_ADAPTER_HOST || DEFAULT_HOST;
  const port = Number(process.env.XNP_SMS_ADAPTER_PORT || DEFAULT_PORT);
  createServer().listen(port, host, () => {
    console.log(`XiaoNaiPing Aliyun SMS adapter listening on http://${host}:${port}`);
  });
}

module.exports = {
  createServer,
  normalizeAliyunPhoneNumber,
  verifyWebhookSignature,
};
