#!/usr/bin/env node
// Suelta un fichero en una zona de drop usando CDP Input.dispatchDragEvent (sin file picker).
//
// Uso: node cdp_drop.js --match <urlSub> --file <ruta> [--find "<texto de la zona>"]
//
// Busca la zona por texto (por defecto "Selecciona archivos"), calcula su centro y emite
// dragEnter → dragOver → drop con `files`. Chrome 90+ acepta rutas absolutas en `files`.

const fs = require('fs');
const path = require('path');
const PORT = process.env.CDP_PORT || 9222;
const argv = process.argv.slice(2);
const arg = (n) => { const i = argv.indexOf(n); return i >= 0 ? argv[i + 1] : undefined; };
const MATCH = arg('--match') || '';
const FILE = arg('--file');
const FIND = arg('--find') || 'Selecciona archivos';

async function main() {
  const list = await (await fetch(`http://localhost:${PORT}/json/list`)).json();
  const tab = list.find(t => t.type === 'page' && t.url.includes(MATCH));
  if (!tab) { console.log('NO_TAB'); process.exit(1); }
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
  await send('Runtime.enable');

  const probe = await send('Runtime.evaluate', {
    expression: `(() => {
      const t = ${JSON.stringify(FIND.toLowerCase())};
      const el = [...document.querySelectorAll('div,section,label,span')].reverse()
        .find(e => (e.innerText || '').trim().toLowerCase().startsWith(t) && e.getBoundingClientRect().width > 100);
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return JSON.stringify({ x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2), w: Math.round(r.width), h: Math.round(r.height) });
    })()`,
    returnByValue: true,
  });
  if (!probe.result?.value) { console.log('ZONA_NO_ENCONTRADA'); process.exit(2); }
  const { x, y, w, h } = JSON.parse(probe.result.value);
  console.log('zona →', x, y, w + 'x' + h);

  const b64 = fs.readFileSync(FILE).toString('base64');
  const data = {
    items: [{ mimeType: 'image/png', data: b64, title: path.basename(FILE), baseURL: 'file://' }],
    files: [FILE],
    dragOperationsMask: 1,
  };
  await send('Input.dispatchDragEvent', { type: 'dragEnter', x, y, data });
  await new Promise(r => setTimeout(r, 400));
  await send('Input.dispatchDragEvent', { type: 'dragOver', x, y, data });
  await new Promise(r => setTimeout(r, 400));
  await send('Input.dispatchDragEvent', { type: 'drop', x, y, data });
  console.log('drop enviado');
  await new Promise(r => setTimeout(r, 4000));

  const chk = await send('Runtime.evaluate', {
    expression: `JSON.stringify({ blobImgs: [...document.querySelectorAll('img')].filter(i => (i.src||'').startsWith('blob:')).length, aviso: (document.body.innerText.match(/(subiendo|procesando|imagen|foto)[^\\n]{0,50}/gi) || []).slice(0, 3) })`,
    returnByValue: true,
  });
  console.log('verificación →', chk.result?.value);
  ws.close();
}
main().catch(e => { console.error('ERR', e.message); process.exit(1); });
