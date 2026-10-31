#!/usr/bin/env node
// Generic CDP client: find a page tab by URL substring, optionally navigate, evaluate JS, print JSON result.
// Requires: Chrome instance with CDP enabled (see SKILL.md — Chrome 136+ needs explicit --user-data-dir),
//           Node 22+ (native WebSocket + fetch, zero deps).
//
// Usage:
//   node cdp_eval.js --match <urlSubstring> [--navigate <url>] [--js <expression>] [--wait <ms>]
//
//   --match     required-ish: tab whose URL contains this substring (default '' = first page tab)
//   --navigate  optional: navigate that tab to this URL first
//   --js        optional: JS expression to evaluate (default: {url, title} JSON)
//   --wait      ms to wait after navigation before evaluating (default 8000)
//
//   CDP_PORT env overrides 9222.
//
// Examples:
//   node cdp_eval.js --match slack.com --js "document.title"
//   node cdp_eval.js --match slack.com --navigate "https://app.slack.com/client/TEAM/CHANNEL" \
//     --js "JSON.stringify({url: location.href, title: document.title})"
//   node cdp_eval.js --match github.com --js "document.querySelectorAll('a').length"

const PORT = process.env.CDP_PORT || 9222;
const argv = process.argv.slice(2);
const arg = (name) => { const i = argv.indexOf(name); return i >= 0 ? argv[i + 1] : undefined; };
const MATCH = arg('--match') || '';
const NAV = arg('--navigate');
const JS = arg('--js') || 'JSON.stringify({url: location.href, title: document.title})';
const WAIT = parseInt(arg('--wait') || '8000', 10);

async function main() {
  const list = await (await fetch(`http://localhost:${PORT}/json/list`)).json();
  const tab = list.find(t => t.type === 'page' && t.url.includes(MATCH));
  if (!tab) { console.log('NO_TAB_MATCHING:', MATCH); process.exit(1); }

  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  let msgId = 0;
  const pending = new Map();
  const send = (method, params = {}) => new Promise((res, rej) => {
    const id = ++msgId;
    pending.set(id, { res, rej });
    ws.send(JSON.stringify({ id, method, params }));
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
  console.error('CDP connected:', tab.title, '|', tab.url);

  await send('Page.enable');
  await send('Runtime.enable');
  if (NAV) {
    await send('Page.navigate', { url: NAV });
    console.error('Navigated:', NAV);
  }
  await new Promise(r => setTimeout(r, WAIT));

  const { result } = await send('Runtime.evaluate', { expression: JS, returnByValue: true });
  const v = result.value;
  console.log(typeof v === 'string' ? v : JSON.stringify(v));
  ws.close();
}

main().catch(e => { console.error('ERROR:', e.message); process.exit(1); });
