#!/usr/bin/env node
// Intercepta el diálogo nativo de subida de ficheros y entrega un archivo sin tocar el Finder.
//
// Uso:
//   node cdp_upload.js --match <urlSubstring> --file <ruta> --click "<selector o índice>"
//
// --click admite:
//   css:<selector>     document.querySelector(sel).click()
//   idx:<n>            n-ésimo button/[role=button] de la página
//   btn:<texto>        el primero cuyo innerText contenga <texto>
//
// Requiere Page.setInterceptFileChooserDialog: el picker no llega a abrirse y el evento
// Page.fileChooserOpened trae el backendNodeId del input real (aunque esté en un shadow root).

const PORT = process.env.CDP_PORT || 9222;
const argv = process.argv.slice(2);
const arg = (n) => { const i = argv.indexOf(n); return i >= 0 ? argv[i + 1] : undefined; };
const MATCH = arg('--match') || '';
const FILE = arg('--file');
const CLICK = arg('--click') || '';

function clickExpr(spec) {
  if (spec.startsWith('css:')) return `document.querySelector(${JSON.stringify(spec.slice(4))}).click()`;
  if (spec.startsWith('idx:')) {
    const n = Number(spec.slice(4));
    return `[...document.querySelectorAll('button,[role=button]')][${n}].click()`;
  }
  if (spec.startsWith('btn:')) {
    const t = JSON.stringify(spec.slice(4).toLowerCase());
    return `(() => { const b=[...document.querySelectorAll('button,[role=button]')].find(e=>(e.innerText||'').toLowerCase().includes(${t})); if(!b) return 'NO_BUTTON'; b.click(); return 'clicked'; })()`;
  }
  return spec;
}

async function main() {
  const list = await (await fetch(`http://localhost:${PORT}/json/list`)).json();
  const tab = list.find(t => t.type === 'page' && t.url.includes(MATCH));
  if (!tab) { console.log('NO_TAB_MATCHING:', MATCH); process.exit(1); }
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  let id = 0;
  const pending = new Map();
  let chooserResolve;
  const chooser = new Promise(r => { chooserResolve = r; });
  const send = (method, params = {}) => new Promise((res, rej) => {
    const mid = ++id;
    pending.set(mid, { res, rej });
    ws.send(JSON.stringify({ id: mid, method, params }));
  });
  ws.onmessage = (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) {
      const { res, rej } = pending.get(m.id);
      pending.delete(m.id);
      m.error ? rej(new Error(m.error.message)) : res(m.result);
      return;
    }
    if (m.method === 'Page.fileChooserOpened') chooserResolve(m.params);
  };
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  await send('Page.enable');
  await send('DOM.enable');
  await send('Runtime.enable');
  await send('Page.setInterceptFileChooserDialog', { enabled: true });

  const r = await send('Runtime.evaluate', { expression: clickExpr(CLICK), returnByValue: true });
  console.log('click →', r.result?.value);

  // Un click programático NO da activación de usuario: los navegadores bloquean el file picker.
  // Se repite con entrada de ratón real en el centro del elemento.
  const rectExpr = CLICK.startsWith('btn:')
    ? `(() => { const t=${JSON.stringify(CLICK.slice(4).toLowerCase())}; const b=[...document.querySelectorAll('button,[role=button]')].find(e=>(e.innerText||'').toLowerCase().includes(t)); if(!b) return null; const r=b.getBoundingClientRect(); return JSON.stringify({x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2)}); })()`
    : CLICK.startsWith('css:')
    ? `(() => { const b=document.querySelector(${JSON.stringify(CLICK.slice(4))}); if(!b) return null; const r=b.getBoundingClientRect(); return JSON.stringify({x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2)}); })()`
    : 'null';
  const rect = await send('Runtime.evaluate', { expression: rectExpr, returnByValue: true });
  if (rect.result?.value) {
    const { x, y } = JSON.parse(rect.result.value);
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 });
    console.log('click real →', x, y);
  }

  const params = await Promise.race([
    chooser,
    new Promise((_, rej) => setTimeout(() => rej(new Error('timeout esperando fileChooserOpened')), 8000)),
  ]);
  console.log('fileChooserOpened →', JSON.stringify({ backendNodeId: params.backendNodeId, mode: params.mode }));

  await send('DOM.setFileInputFiles', { files: [FILE], backendNodeId: params.backendNodeId });
  console.log('subido →', FILE);
  await new Promise(r2 => setTimeout(r2, 3000));
  const chk = await send('Runtime.evaluate', {
    expression: `JSON.stringify({ imgs: [...document.querySelectorAll('img')].filter(i=>i.src.startsWith('blob:')||i.src.startsWith('data:')).length, texto: document.body.innerText.slice(0,120) })`,
    returnByValue: true,
  });
  console.log('verificación →', chk.result?.value);
  ws.close();
}

main().catch(e => { console.error('ERR', e.message); process.exit(1); });
