// Comprobaciones de accesibilidad de la interfaz (las que no cubre axe):
// anchos móviles, desborde con el texto al 200 %, recorrido con teclado, enlace de salto,
// tabla alternativa del mapa y respeto por «movimiento reducido».
//
// Uso:  NODE_PATH=$(npm root -g) node scripts/a11y-check.mjs http://localhost:3100 <contraseña-superadmin>
// (la contraseña es opcional: sin ella solo se comprueban las páginas públicas y el login)
import { chromium } from "playwright";

const BASE = process.argv[2] ?? "http://localhost:3100";
const PASS = process.argv[3] ?? "";
const RUTAS = ["/mapa", "/puertos", "/fuentes", "/asistente", "/glosario", "/api-docs", "/accesibilidad", "/", "/login"];
const ANCHOS = [320, 360, 390, 768];

const problemas = [];
const browser = await chromium.launch();

/** Mide desbordes horizontales y elementos que se salen del ancho de la ventana. */
const medir = (page) => page.evaluate(() => {
  const d = document.documentElement;
  const fugas = [...document.querySelectorAll("body *")]
    .filter((e) => {
      const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
      return r.width > 0 && r.right > window.innerWidth + 2 && s.position !== "fixed" && s.position !== "absolute"
        && !e.closest(".scroll-x, .lp-isobaths, .lp-draft, .lp-video, pre");
    })
    .slice(0, 5).map((e) => e.tagName + "." + (typeof e.className === "string" ? e.className.split(" ").slice(0, 2).join(".") : ""));
  return { scrollW: d.scrollWidth, clientW: d.clientWidth, fugas };
});

async function entrar(ctx) {
  if (!PASS) return;
  const p = await ctx.newPage();
  await p.goto(BASE + "/login");
  const estado = await p.evaluate(async ([pass]) => (await fetch("/api/auth/login", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ email: "you@example.com", password: pass }) })).status, [PASS]);
  if (estado !== 200) problemas.push(`LOGIN falló (${estado}): revisa la contraseña`);
  await p.close();
}

// ---------- 1) anchos móviles ----------
const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
await entrar(ctx);
const page = await ctx.newPage();
for (const w of ANCHOS) {
  await page.setViewportSize({ width: w, height: 780 });
  for (const ruta of RUTAS) {
    await page.goto(BASE + ruta);
    await page.waitForTimeout(1100);
    const m = await medir(page);
    if (m.scrollW > m.clientW + 2 || m.fugas.length) problemas.push(`MÓVIL ${w}px ${ruta}: scrollW=${m.scrollW}/${m.clientW} fugas=${JSON.stringify(m.fugas)}`);
  }
}

// ---------- 2) texto al 200 % (equivalente al «solo texto» de Firefox) ----------
await page.setViewportSize({ width: 1280, height: 900 });
for (const ruta of RUTAS) {
  await page.goto(BASE + ruta);
  await page.waitForTimeout(900);
  await page.addStyleTag({ content: "html { font-size: 200% !important; }" });
  await page.waitForTimeout(400);
  const m = await medir(page);
  if (m.scrollW > m.clientW + 2 || m.fugas.length) problemas.push(`TEXTO 200 % ${ruta}: scrollW=${m.scrollW}/${m.clientW} fuera=${JSON.stringify(m.fugas)}`);
}

// ---------- 3) teclado: primer tabulador = saltar al contenido ----------
await page.goto(BASE + "/mapa");
await page.waitForTimeout(1500);
await page.keyboard.press("Tab");
const primero = await page.evaluate(() => { const a = document.activeElement; return { clase: String(a.className), texto: (a.textContent ?? "").trim().slice(0, 30) }; });
if (!/saltar/.test(primero.clase)) problemas.push(`TECLADO: el primer tabulador no es «saltar al contenido»: ${JSON.stringify(primero)}`);
else {
  await page.keyboard.press("Enter");
  await page.waitForTimeout(300);
  const destino = await page.evaluate(() => ({ tag: document.activeElement.tagName, id: document.activeElement.id }));
  if (destino.id !== "contenido") problemas.push(`TECLADO: el salto no deja el foco en #contenido: ${JSON.stringify(destino)}`);
}

// ---------- 4) mapa: la alternativa textual funciona con teclado ----------
const alt = await page.evaluate(async () => {
  const det = document.querySelector("#alternativa-mapa");
  if (!det) return { ok: false, motivo: "no existe la tabla alternativa" };
  det.open = true;
  const b = det.querySelector("tbody button");
  if (!b) return { ok: false, motivo: "no hay botón de situar" };
  b.focus();
  const enfocado = document.activeElement === b;
  b.click();
  await new Promise((r) => setTimeout(r, 1200));
  const panel = document.querySelector('[aria-live="polite"]');
  return { ok: true, enfocado, filas: det.querySelectorAll("tbody tr").length, panel: (panel?.textContent ?? "").trim().slice(0, 60) };
});
if (!alt.ok || !alt.enfocado || !alt.panel) problemas.push(`MAPA · alternativa textual: ${JSON.stringify(alt)}`);

// ---------- 5) movimiento reducido ----------
const ctx2 = await browser.newContext({ viewport: { width: 1280, height: 900 }, reducedMotion: "reduce" });
await entrar(ctx2);
const p2 = await ctx2.newPage();
await p2.goto(BASE + "/");
const rm = await p2.evaluate(() => matchMedia("(prefers-reduced-motion: reduce)").matches);
if (!rm) problemas.push("MOVIMIENTO REDUCIDO: el navegador no reporta la preferencia");
else console.log(`· movimiento reducido respetado · filas de la tabla alternativa: ${alt.filas}`);

await browser.close();
if (problemas.length) { console.log("PROBLEMAS:\n" + problemas.join("\n")); process.exit(1); }
console.log(`RESULTADO: OK · móvil ${ANCHOS.join("/")} px, texto al 200 %, teclado, tabla alternativa del mapa y movimiento reducido`);
