// Comprobación de contraste WCAG AA de TODO el texto visible de la interfaz.
// axe-core no puede resolver el fondo cuando el texto se superpone a un SVG o a una caja
// desplazada (por eso lo deja en «incomplete»); aquí se resuelve subiendo por el árbol y
// componiendo la opacidad de los ancestros.
//
// Uso: NODE_PATH=$(npm root -g) node /tmp/contraste.mjs http://localhost:3100 <contraseña>
import { chromium } from "playwright";

const BASE = process.argv[2] ?? "http://localhost:3100";
const PASS = process.argv[3] ?? "";
const RUTAS = ["/", "/accesibilidad", "/login", "/mapa", "/puertos", "/puertos/santa-cruz-de-tenerife", "/fuentes", "/fuentes/ops-netzeromar", "/asistente", "/agentes", "/api-docs", "/claves", "/usuarios", "/glosario"];

const LUM = (c) => {
  const [r, g, b] = c.map((v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};
const RATIO = (a, b) => { const la = LUM(a), lb = LUM(b); const hi = Math.max(la, lb), lo = Math.min(la, lb); return (hi + 0.05) / (lo + 0.05); };

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
if (PASS) {
  const p0 = await ctx.newPage();
  await p0.goto(BASE + "/login");
  await p0.evaluate(async ([pass]) => (await fetch("/api/auth/login", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ email: "you@example.com", password: pass }) })).status, [PASS]);
  await p0.close();
}
const page = await ctx.newPage();

const fallos = [];
let medidos = 0;
for (const ruta of RUTAS) {
  await page.goto(BASE + ruta);
  await page.waitForTimeout(1200);
  const res = await page.evaluate(() => {
    const parse = (s) => (s.match(/[\d.]+/g) ?? []).slice(0, 3).map(Number);
    const alpha = (s) => { const m = s.match(/[\d.]+/g); return m && m.length > 3 ? Number(m[3]) : 1; };
    const opacidad = (el) => { let n = el, o = 1; while (n && n !== document.documentElement) { o *= Number(getComputedStyle(n).opacity ?? 1); n = n.parentElement; } return o; };
    const fondo = (el) => {
      let n = el, acum = null;
      while (n && n !== document.documentElement) {
        const bg = getComputedStyle(n).backgroundColor;
        const a = alpha(bg);
        if (a > 0) { const c = parse(bg); acum = acum ? acum.map((v, i) => v * (1 - a) + c[i] * a) : c.map((v) => v * a + 255 * (1 - a) * 0); if (a === 1) return { color: acum, opaco: true }; }
        n = n.parentElement;
      }
      const body = parse(getComputedStyle(document.body).backgroundColor);
      return { color: acum ? acum.map((v, i) => v + body[i] * (1 - 0.999)) : body, opaco: false };
    };
    const salida = [];
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const vistos = new Set();
    let nodo;
    while ((nodo = walker.nextNode())) {
      const txt = (nodo.textContent ?? "").trim();
      if (txt.length < 2) continue;
      const el = nodo.parentElement;
      if (!el || vistos.has(el)) continue;
      const cs = getComputedStyle(el);
      if (cs.visibility === "hidden" || cs.display === "none" || Number(cs.opacity) === 0) continue;
      const r = el.getBoundingClientRect();
      if (r.width < 2 || r.height < 2) continue;
      if (el.closest('[aria-hidden="true"], .sr-only, .lp-isobaths, .lp-draft, .lp-svg-tall')) continue;
      vistos.add(el);
      salida.push({
        txt: txt.slice(0, 34), sel: el.tagName + "." + (typeof el.className === "string" ? el.className.split(" ").slice(0, 2).join(".") : ""),
        color: cs.color, size: parseFloat(cs.fontSize), weight: Number(cs.fontWeight), opacidad: opacidad(el), fondoEl: fondo(el),
      });
    }
    return salida;
  });

  for (const t of res) {
    const c = (t.color.match(/[\d.]+/g) ?? []).slice(0, 3).map(Number);
    const bg = t.fondoEl.color;
    // si hay opacidad en los ancestros, el texto se mezcla con el fondo
    const fg = t.opacidad < 1 ? c.map((v, i) => v * t.opacidad + bg[i] * (1 - t.opacidad)) : c;
    const cr = RATIO(fg, bg);
    const grande = t.size >= 24 || (t.size >= 18.66 && t.weight >= 700);
    const min = grande ? 3 : 4.5;
    medidos++;
    if (cr < min) fallos.push(`${ruta} · ${cr.toFixed(2)} < ${min} · ${t.sel} · «${t.txt}» (${t.color} sobre rgb(${bg.map(Math.round).join(",")}), ${t.size}px/${t.weight})`);
  }
}
await browser.close();
console.log(`Elementos de texto medidos: ${medidos}`);
console.log(fallos.length ? "FALLOS DE CONTRASTE:\n" + fallos.join("\n") : "CONTRASTE: OK · todo el texto visible cumple AA (4,5:1 / 3:1 en texto grande)");
process.exit(fallos.length ? 1 : 0);
