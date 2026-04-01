const DEFAULT_BASE = process.env.BASE_URL || 'http://localhost:3000';
const ADMIN_TOKEN = process.env.ADMIN_TOKEN || '';

async function callGet() {
  try {
    const headers: Record<string, string> = {};
    if (ADMIN_TOKEN) {
      headers.Authorization = `Bearer ${ADMIN_TOKEN}`;
    }
    const res = await fetch(`${DEFAULT_BASE}/ops/logging/verbosity`, {
      method: 'GET',
      headers
    });
    const text = await res.text();
    console.log('[verify_verbosity_endpoint] GET status', res.status, 'body:', text);
    return res.status;
  } catch (e) {
    console.error('[verify_verbosity_endpoint] GET failed:', e);
    return null;
  }
}

async function callPost() {
  try {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (ADMIN_TOKEN) {
      headers.Authorization = `Bearer ${ADMIN_TOKEN}`;
    }
    const res = await fetch(`${DEFAULT_BASE}/ops/logging/verbosity`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ verbosity: 'debug' })
    });
    const text = await res.text();
    console.log('[verify_verbosity_endpoint] POST status', res.status, 'body:', text);
    return res.status;
  } catch (e) {
    console.error('[verify_verbosity_endpoint] POST failed:', e);
    return null;
  }
}

(async () => {
  console.log('[verify_verbosity_endpoint] Testing', DEFAULT_BASE);
  const g = await callGet();
  const p = await callPost();
  const g2 = await callGet();

  const result = { beforeGet: g, post: p, afterGet: g2 };
  console.log('[verify_verbosity_endpoint] Result:', JSON.stringify(result));

  if ((p && p >= 200 && p < 300) || (g && g >= 200 && g < 300)) {
    process.exit(0);
  }
  process.exit(6);
})();
