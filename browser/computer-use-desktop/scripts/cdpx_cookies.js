#!/usr/bin/env node
// Extrae las cookies de un dominio desde un navegador con CDP y las guarda en formato
// CDP/Puppeteer para pasárselas a Lightpanda con --cookie.
//
// Uso: node cdpx_cookies.js --port 9222 --match linkedin.com --domain linkedin.com --out <ruta>
//
// Nunca imprime valores: solo cuenta y lista los NOMBRES de las cookies guardadas.

const fs = require('fs');
const argv = process.argv.slice(2);
const arg = (n) => { const i = argv.indexOf(n); return i >= 0 ? argv[i + 1] : undefined; };
const PORT = arg('--port') || '9222';
const MATCH = arg('--match') || '';
const DOMAIN = arg('--domain') || MATCH;
const OUT = arg('--out');

async function main() {
  const list = await (await fetch(`http://localhost:${PORT}/json/list`)).json();
  const tab = list.find(t => t.type === 'page' && t.url.includes(MATCH));
  if (!tab) { console.log('NO_TAB_MATCHING:', MATCH); process.exit(1); }
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  let id = 0; const pending = new Map();
  const send = (m, p = {}) => new Promise((res, rej) => {
    const mid = ++id; pending.set(mid, { res, rej });
    ws.send(JSON.stringify({ id: mid, method: m, params: p }));
  });
  ws.onmessage = (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) {
      const { res, rej } = pending.get(m.id); pending.delete(m.id);
      m.error ? rej(new Error(m.error.message)) : res(m.result);
    }
  };
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  await send('Network.enable');           // sin esto getAllCookies devuelve vacío
  await send('Page.enable');
  const { cookies } = await send('Network.getAllCookies');
  const mine = cookies.filter(c => c.domain.includes(DOMAIN));
  const slim = mine.map(c => ({
    name: c.name,
    value: c.value,
    domain: c.domain,
    path: c.path || '/',
    expires: c.expires > 0 ? c.expires : -1,
    httpOnly: !!c.httpOnly,
    secure: !!c.secure,
    sameSite: c.sameSite || 'Lax',
  }));
  fs.writeFileSync(OUT, JSON.stringify(slim, null, 1), { mode: 0o600 });
  fs.chmodSync(OUT, 0o600);
  console.log(`cookies totales del navegador: ${cookies.length}`);
  console.log(`guardadas para ${DOMAIN}: ${slim.length} en ${OUT}`);
  console.log('nombres:', slim.map(c => c.name).join(', ').slice(0, 400));
  ws.close();
}
main().catch(e => { console.error('ERR', e.message); process.exit(1); });
