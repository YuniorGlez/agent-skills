#!/usr/bin/env node
// Lee el muro de X desde Lightpanda con cookies inyectadas, haciendo scroll.
// Uso: node lp_xwall.js --port 9223 --iters 5 [--out fichero.json]
//
// Requiere servir Lightpanda con --cookie <fichero de cookies>.
// Extrae {autor, handle, texto} de cada <article> y deduplica por texto.

const fs = require('fs');
const argv = process.argv.slice(2);
const arg = (n) => { const i = argv.indexOf(n); return i >= 0 ? argv[i + 1] : undefined; };
const PORT = arg('--port') || '9223';
const ITERS = Number(arg('--iters') || '5');
const OUT = arg('--out') || 'out_xwall.json';
const t0 = Date.now();

async function main() {
  const ver = await (await fetch(`http://127.0.0.1:${PORT}/json/version`)).json();
  const ws = new WebSocket(ver.webSocketDebuggerUrl);
  let id = 0; const pending = new Map();
  const send = (m, p = {}, sid) => new Promise((res, rej) => {
    const mid = ++id; pending.set(mid, { res, rej });
    const msg = { id: mid, method: m, params: p };
    if (sid) msg.sessionId = sid;
    ws.send(JSON.stringify(msg));
  });
  ws.onmessage = (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) {
      const { res, rej } = pending.get(m.id); pending.delete(m.id);
      m.error ? rej(new Error(JSON.stringify(m.error).slice(0, 140))) : res(m.result);
    }
  };
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });

  const { targetId } = await send('Target.createTarget', { url: 'https://x.com/home' });
  const { sessionId } = await send('Target.attachToTarget', { targetId, flatten: true });
  await new Promise(r => setTimeout(r, 6000));

  const seen = new Map();
  const grab = `(() => {
    const out = [];
    document.querySelectorAll('article').forEach(a => {
      const txt = (a.innerText || '').replace(/\\s+/g, ' ').trim();
      if (!txt) return;
      const h = txt.match(/@[A-Za-z0-9_]{2,20}/);
      out.push({ handle: h ? h[0] : '', texto: txt.slice(0, 400) });
    });
    return JSON.stringify(out);
  })()`;

  for (let i = 0; i < ITERS; i++) {
    const r = await send('Runtime.evaluate', { expression: grab, returnByValue: true }, sessionId);
    const batch = JSON.parse(r.result.value || '[]');
    let nuevos = 0;
    for (const p of batch) {
      const key = p.texto.slice(0, 140);
      if (!seen.has(key)) { seen.set(key, p); nuevos++; }
    }
    console.log(`  iter ${i + 1}: articles=${batch.length} nuevos=${nuevos} total=${seen.size} (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
    await send('Runtime.evaluate', { expression: 'window.scrollBy(0, 1600)', returnByValue: true }, sessionId);
    await new Promise(r => setTimeout(r, 2200));
  }

  const posts = [...seen.values()];
  fs.writeFileSync(OUT, JSON.stringify(posts, null, 1));
  console.log(`\n${posts.length} posts únicos en ${((Date.now() - t0) / 1000).toFixed(1)}s → ${OUT}`);
  for (const p of posts.slice(0, 8)) console.log(`  ${p.handle.padEnd(18)} ${p.texto.slice(0, 90)}`);
  await send('Target.closeTarget', { targetId });
  ws.close();
}
main().catch(e => { console.error('ERR', e.message); process.exit(1); });
