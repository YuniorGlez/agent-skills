#!/usr/bin/env node
// CDP contra Lightpanda: no expone /json/new, hay que crear el target por websocket.
//
// Uso: node lp_cdp.js --port 9223 --url <url> --js "<expr>"
//
// Target.createTarget + Target.attachToTarget({flatten:true}) y luego Runtime.evaluate
// con el sessionId de la sesión plana.

const argv = process.argv.slice(2);
const arg = (n) => { const i = argv.indexOf(n); return i >= 0 ? argv[i + 1] : undefined; };
const PORT = arg('--port') || process.env.CDP_PORT || '9223';
const URL = arg('--url');
const WAIT = Number(arg('--wait') || '3000');
const COOKIE = arg('--cookie');
const JS = arg('--js') || 'JSON.stringify({title:document.title,url:location.href})';

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
      m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result);
    }
  };
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  console.log('browser:', ver.Browser);

  const { targetId } = await send('Target.createTarget', { url: URL });
  console.log('target:', targetId);
  const { sessionId } = await send('Target.attachToTarget', { targetId, flatten: true });
  console.log('session:', sessionId);

  await new Promise(r => setTimeout(r, WAIT));
  const out = await send('Runtime.evaluate', { expression: JS, returnByValue: true }, sessionId);
  console.log('js →', JSON.stringify(out.result?.value ?? null).slice(0, 500));
  await send('Target.closeTarget', { targetId });
  ws.close();
}
main().catch(e => { console.error('ERR', e.message); process.exit(1); });
