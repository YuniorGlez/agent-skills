#!/usr/bin/env node
// CDP driver con pasos encadenados sobre una pestaña concreta.
//
// Uso:
//   node cdp_do.js --match <urlSubstring> "js:<expr>" "insert:<texto>" "key:Enter" "wait:1000" ...
//
// Pasos:
//   js:<expr>            evalúa JS y devuelve el valor (true = continue)
//   insert:<texto>       Input.insertText en el foco actual (respeta contenteditable)
//   key:<Name>           Input.dispatchKeyEvent con teclas: Enter, ArrowDown, Escape, Tab, Backspace
//   clickxy:<x>,<y>      clic de ratón real en coordenadas de viewport
//   upload:<sel>|<ruta>  DOM.setFileInputFiles sobre input[type=file]
//   wait:<ms>
//
// Imprime el resultado de cada paso. CDP_PORT por defecto 9222.

const PORT = process.env.CDP_PORT || 9222;
const argv = process.argv.slice(2);
const mi = argv.indexOf('--match');
const MATCH = mi >= 0 ? argv[mi + 1] : '';
const steps = argv.filter((a, i) => a !== '--match' && i !== mi + 1);

const KEYS = {
  Enter: { key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13, text: '\r' },
  Tab: { key: 'Tab', code: 'Tab', windowsVirtualKeyCode: 9 },
  Escape: { key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 },
  ArrowDown: { key: 'ArrowDown', code: 'ArrowDown', windowsVirtualKeyCode: 40 },
  ArrowUp: { key: 'ArrowUp', code: 'ArrowUp', windowsVirtualKeyCode: 38 },
  Backspace: { key: 'Backspace', code: 'Backspace', windowsVirtualKeyCode: 8 },
  Space: { key: ' ', code: 'Space', windowsVirtualKeyCode: 32, text: ' ' },
};

async function main() {
  const list = await (await fetch(`http://localhost:${PORT}/json/list`)).json();
  const tab = list.find(t => t.type === 'page' && t.url.includes(MATCH));
  if (!tab) { console.log('NO_TAB_MATCHING:', MATCH); process.exit(1); }
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  let id = 0;
  const pending = new Map();
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
    }
  };
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  await send('Runtime.enable');
  await send('Input.enable').catch(() => {});
  console.error('tab:', tab.title.slice(0, 40), '|', tab.url.slice(0, 60));

  for (const step of steps) {
    const i = step.indexOf(':');
    const kind = step.slice(0, i);
    const payload = step.slice(i + 1);
    if (kind === 'js') {
      const r = await send('Runtime.evaluate', { expression: payload, returnByValue: true, awaitPromise: true });
      console.log('js →', JSON.stringify(r.result?.value ?? r.result?.description ?? null).slice(0, 400));
    } else if (kind === 'insert') {
      await send('Input.insertText', { text: payload });
      console.log('insert →', payload.slice(0, 60));
    } else if (kind === 'key') {
      const k = KEYS[payload] || { key: payload, code: payload };
      await send('Input.dispatchKeyEvent', { type: 'keyDown', ...k });
      await send('Input.dispatchKeyEvent', { type: 'keyUp', ...k });
      console.log('key →', payload);
    } else if (kind === 'clickxy') {
      const [x, y] = payload.split(',').map(Number);
      await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 });
      await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 });
      console.log('click →', x, y);
    } else if (kind === 'upload') {
      const [sel, file] = payload.split('|');
      await send('DOM.enable');
      const { root } = await send('DOM.getDocument', { depth: -1, pierce: true });
      const { nodeId } = await send('DOM.querySelector', { nodeId: root.nodeId, selector: sel });
      if (!nodeId) { console.log('upload → input no encontrado:', sel); continue; }
      await send('DOM.setFileInputFiles', { nodeId, files: [file] });
      console.log('upload →', file);
    } else if (kind === 'wait') {
      await new Promise(r => setTimeout(r, Number(payload)));
    } else {
      console.log('paso desconocido:', step.slice(0, 40));
    }
  }
  ws.close();
}

main().catch(e => { console.error('ERR', e.message); process.exit(1); });
