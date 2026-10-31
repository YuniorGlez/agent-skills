#!/usr/bin/env node
// Carga N URLs en paralelo contra Lightpanda y mide tiempo y RAM del proceso servidor.
// Uso: node lp_parallel.js --port 9223 --n 8

const { execSync } = require('child_process');
const argv = process.argv.slice(2);
const arg = (n) => { const i = argv.indexOf(n); return i >= 0 ? argv[i + 1] : undefined; };
const PORT = arg('--port') || '9223';
const N = Number(arg('--n') || '8');
const URLS = [
  'https://news.ycombinator.com',
  'https://example.com',
  'https://the agency.com',
  'https://www.linkedin.com/',
  'https://github.com/lightpanda-io/browser',
  'https://vercel.com',
  'https://www.wikipedia.org',
  'https://developer.mozilla.org',
];

function rssMB() {
  try {
    const pid = execSync("pgrep -f 'lightpanda serve' | head -1").toString().trim();
    const kb = Number(execSync(`ps -o rss= -p ${pid}`).toString().trim());
    return Math.round(kb / 1024);
  } catch { return null; }
}

async function main() {
  const ver = await (await fetch(`http://127.0.0.1:${PORT}/json/version`)).json();
  const ws = new WebSocket(ver.webSocketDebuggerUrl);
  let id = 0; const pending = new Map();
  const send = (method, params = {}, sessionId) => new Promise((res, rej) => {
    const mid = ++id; pending.set(mid, { res, rej });
    const msg = { id: mid, method, params };
    if (sessionId) msg.sessionId = sessionId;
    ws.send(JSON.stringify(msg));
  });
  ws.onmessage = (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) {
      const { res, rej } = pending.get(m.id); pending.delete(m.id);
      m.error ? rej(new Error(JSON.stringify(m.error).slice(0, 120))) : res(m.result);
    }
  };
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  const base = rssMB();
  console.log('RAM en reposo:', base, 'MB');

  const t0 = Date.now();
  const jobs = URLS.slice(0, N).map(async (url) => {
    const { targetId } = await send('Target.createTarget', { url });
    const { sessionId } = await send('Target.attachToTarget', { targetId, flatten: true });
    await new Promise(r => setTimeout(r, 2500));
    const r = await send('Runtime.evaluate', {
      expression: 'JSON.stringify({t:document.title, n:(document.body.innerText||"").length})',
      returnByValue: true,
    }, sessionId);
    return { url, ...JSON.parse(r.result.value || '{}') };
  });
  const results = await Promise.all(jobs);
  const secs = ((Date.now() - t0) / 1000).toFixed(1);
  const peak = rssMB();
  for (const r of results) console.log(`  ${(r.t || '—').slice(0, 40).padEnd(42)} texto=${r.n}`);
  console.log(`\n${results.length} páginas en ${secs}s · RAM pico servidor: ${peak} MB (base ${base})`);
  ws.close();
}
main().catch(e => { console.error('ERR', e.message); process.exit(1); });
