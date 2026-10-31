#!/usr/bin/env node
// Búsqueda avanzada de repositorios de GitHub a través de Lightpanda (CDP), sin token ni API.
//
// Uso:
//   node gh_search_lp.js --port 9225 --query "topic:ai-agents pushed:>2026-10-16" --pages 2 --out repos.json
//
// La búsqueda de GitHub no viene en el HTML inicial: hay que ejecutar JS, así que `fetch` no sirve
// y esto va por Target.createTarget + Runtime.evaluate. Extrae nombre, descripción, lenguaje,
// estrellas y "Updated …" de cada tarjeta de resultado.

const fs = require('fs');
const argv = process.argv.slice(2);
const arg = (n) => { const i = argv.indexOf(n); return i >= 0 ? argv[i + 1] : undefined; };
const PORT = arg('--port') || '9225';
const QUERY = arg('--query') || 'topic:ai-agents pushed:>2026-10-16';
const PAGES = Number(arg('--pages') || '1');
const OUT = arg('--out') || 'gh_repos.json';
const t0 = Date.now();

const url = (p) =>
  `https://github.com/search?q=${encodeURIComponent(QUERY)}&type=repositories&s=updated&o=desc&p=${p}`;

const EXTRACT = `(() => {
  const list = document.querySelector('div[data-testid=results-list]');
  if (!list) return JSON.stringify({ error: 'sin resultados' });
  const out = [];
  for (const card of list.children) {
    const t = (card.innerText || '').replace(/\\s+/g, ' ').trim();
    if (!t) continue;
    const name = (t.match(/^([\\w.-]+\\/[\\w.-]+)/) || [])[1] || '';
    const stars = (t.match(/·\\s*([\\d.,]+k?)\\s*·\\s*Updated/) || [])[1] || '';
    const updated = ((t.match(/Updated ([^·]+)/i) || [])[1] || '').replace(/\\s*Star\\b.*$/i, '').trim();
    const lang = (t.match(/·\\s*([A-Za-z+#]+)\\s*·\\s*[\\d.,]+k?/) || [])[1] || '';
    out.push({ name, stars, lang, updated, desc: t.slice(name.length, 160).trim() });
  }
  return JSON.stringify(out);
})()`;

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

  const seen = new Map();
  for (let p = 1; p <= PAGES; p++) {
    const { targetId } = await send('Target.createTarget', { url: url(p) });
    const { sessionId } = await send('Target.attachToTarget', { targetId, flatten: true });
    await new Promise(r => setTimeout(r, 7000));
    const r = await send('Runtime.evaluate', { expression: EXTRACT, returnByValue: true }, sessionId);
    let batch = [];
    try { batch = JSON.parse(r.result.value || '[]'); } catch { console.log('  página', p, 'sin JSON'); }
    if (batch.error) { console.log('  página', p, batch.error); }
    let n = 0;
    for (const repo of batch) {
      if (repo.name && !seen.has(repo.name)) { seen.set(repo.name, repo); n++; }
    }
    console.log(`  pág ${p}: ${batch.length} tarjetas, ${n} nuevas, total ${seen.size} (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
    await send('Target.closeTarget', { targetId });
  }

  const repos = [...seen.values()];
  fs.writeFileSync(OUT, JSON.stringify(repos, null, 1));
  console.log(`\n${repos.length} repositorios → ${OUT} (${((Date.now() - t0) / 1000).toFixed(1)}s)`);
  for (const r of repos.slice(0, 10)) {
    console.log(`  ${r.name.padEnd(38)} ★${(r.stars || '?').padEnd(5)} ${(r.lang || '').padEnd(10)} ${r.updated}`);
  }
  ws.close();
}
main().catch(e => { console.error('ERR', e.message); process.exit(1); });
