---
name: agent-browser
description: "Browser automation or a11y audits: use agent-browser CLI."
version: 1.0.0
author: Hermes + el operador
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [browser, a11y, wcag, scraping, testing, qa, agent-browser]
---

# agent-browser — navegación agéntica + auditorías a11y (Vercel Labs)

## Selección de herramienta de navegación (stack actual, 13-ago-2026)

| Escenario | Herramienta |
|---|---|
| Extracción markdown/texto de URLs en lote, scraping/RAG structure-first, crons sin daemon | **Lightpanda** o **moli** (motores headless propios, sin Chromium) |
| Leer webs con **sesión del usuario** (X, LinkedIn) sin abrir ventana | **Lightpanda** + cookies exportadas por CDP (`computer-use-desktop/references/lightpanda.md`) |
| Auditorías a11y WCAG | **agent-browser** (axe-core nativo) |
| Navegación determinista con Chrome real (snapshot con refs @e1, clicks, formularios, auth de sesión) | **agent-browser** |
| Dumps DOM CLI crudos | **chrome-headless-shell** de Playwright (Chrome de Google se cuelga en headless, ver pitfalls) |
| Tareas agénticas abiertas ("haz X en esta web" con LLM decidiendo) | **browser-use** (reserva) |
| Monitorización visual / screenshots de fidelidad / canvas-WebGL | **Chrome/Playwright reales** (ningún motor propio: no renderizan) |

Decisión tomada en el benchmark moli (13-ago-2026): moli gana para structure-first por 6.5x menos
memoria y salidas agente-first nativas; no sustituye a Chromium para lo visual. Informe:
`~/projects/<bench>/informe.html`.

**Lightpanda (medido 31-oct-2026, 1.0.2)** — mismo nicho que moli, mejores números en esta máquina:
example.com 0,42 s / 30,5 MB frente a 0,62 s / 91,1 MB de chrome-headless-shell; ocho páginas en
paralelo en 3,2 s con 175 MB de pico. Dos trampas: `fetch --dump markdown` no espera a las SPA
(47 bytes en una home Next frente a 9.618 caracteres leídos por CDP) y puede devolver **0 bytes con
exit 0** cuando el sitio bloquea. Detalle y comparativa por URL:
`computer-use-desktop/references/lightpanda.md`.

## Instalación / actualización (ya hecha en el Mac de el operador)

CLI nativo en Rust para automatizar navegador (testing, scraping, formularios) y auditorías
WCAG con axe-core. Decidido en el sprint 30d (8-ago-2026) frente a browser-use:
**agent-browser gana** por (1) comando `a11y` nativo con axe-core vendido (browser-use no lo
tiene como CLI), (2) output compacto → menos tokens (read = 0.5KB, snapshot = 4KB),
(3) determinista y scripteable para crons, (4) sin coste LLM para audits/scraping, (5) stack
Node/Rust, sin runtime Python extra. browser-use queda como reserva solo para tareas agénticas
abiertas ("haz X en esta web" con LLM decidiendo) — no instalado.

```bash
brew upgrade agent-browser      # vía CORRECTA: la instalación es de Homebrew (/opt/homebrew/bin)
agent-browser --version         # 22-oct-2026: 0.39.1 (Homebrew va 1 release por detrás de npm)
agent-browser install           # descarga Chrome for Testing (1ª vez; detecta Chrome existente)
```

- ⚠️ **NO instalar con `npm i -g agent-browser` en esta máquina**: `~/.local/bin` va antes en el PATH y
  el `npm` shadowea al de Homebrew → quedarían dos binarios y el linked de brew roto (brecha de
  versiones que `--version` no delata). Actualizar siempre con `brew upgrade`.
- Tras cada upgrade, `brew info agent-browser` da la versión de Homebrew y el tweet de @ctatedev la de
  npm: puede haber 1 release de diferencia (0.39.2 salió el mismo día que brew servía 0.39.1).
- **Smoke test tras actualizar** (30 s): `agent-browser close --all` + `agent-browser a11y
  https://la agencia.com --tags wcag2a,wcag2aa` debe devolver una línea `axe-core … violations/N
  passes/M`, y un `batch --bail "open URL" "get title" "snapshot -i" "close"` debe salir con exit 0.

## Novedades 0.36 → 0.39 (22-oct-2026, verificado en esta máquina)

- **`agent-browser skills`** — guías que viajan DENTRO del CLI y siempre van con la versión instalada:
  `skills get core --full` (referencia completa de comandos, mejor que adivinar flags) y especializadas:
  `dogfood` (explorar y cazar bugs/UX de una web), `derive-client` (reconstruir la API interna de un
  sitio grabando el tráfico), `slack`, `electron`, **`protected-vercel-deployments`** (deployments de
  Vercel con Deployment Protection — el muro de los informes), `vercel-sandbox`, `agentcore`.
  Leer la que toque antes de improvisar.
- **`snapshot --delta`** (18-oct-2026): devuelve solo lo que cambió desde el último snapshot — 73×
  menos tokens rellenando un formulario. El delta se resetea entre sesiones: para comparar horas
  después, guardar el snapshot a fichero y usar `diff snapshot --baseline last.txt`.
- **Seguridad de políticas**: una política inválida ahora DENIEGA (antes un typo abría todo), los
  redirects bloqueados devuelven error explícito (el agente sabe que lo pararon en vez de creer que la
  página está vacía) y hay validación estricta de argumentos MCP.
- Sesiones CDP persistentes, clicks/refs más robustos y arreglo de cuelgues en peticiones de red.

## Auditoría a11y (caso de uso principal)
```bash
agent-browser a11y https://la agencia.com --tags wcag2a,wcag2aa          # human-readable
agent-browser a11y https://la agencia.com --tags wcag2a,wcag2aa --json   # estructurado
agent-browser a11y --selector "#main"                                 # scope a subtree
```
- Lote reproducible: `~/.hermes/scripts/a11y_audit.sh [url...]` → JSONs + `resumen.md` en
  `~/projects/<bench>/audits/`. Sin args audita el lote la agencia
  (la agencia.com, academia.la agencia.com, localhost:3050).
- Resultados reales 8-ago-2026: la agencia.com 1 serious (color-contrast) + 1 incomplete, 22
  passes · academia.la agencia.com 2 violaciones (1 CRITICAL `select-name` en el select de
  idioma + color-contrast), 19 passes · SonicFlow local 0 violaciones, 20 passes.

## Navegación determinista (testing/scraping/formularios)
```bash
agent-browser open https://la agencia.com     # lanza + navega
agent-browser snapshot                     # accessibility tree con refs (@e1...) — ideal para agentes
agent-browser click @e2                    # clicar por ref
agent-browser fill @e3 "test@example.com"  # rellenar por ref
agent-browser find role button click --name "Submit"   # localizador semántico
agent-browser get text @e1 · get title · get url · get count "a"
agent-browser read https://example.com     # texto agente-friendly (markdown, 0.5KB)
agent-browser screenshot page.png --full   # o --annotate (labels numerados para vision)
agent-browser pdf out.pdf
agent-browser close
```
- **batch** (patrón cron, una sola invocación): `agent-browser batch --bail "open URL" "get title" "snapshot -i" "close"` — 0.4s total.
- **read**: sin lanzar Chrome; manda `Accept: text/markdown`, prueba `.md`, `llms.txt`. Con URL
  omitida lee el DOM renderizado de la pestaña activa (incluye estado auth).

## Visión + scroll — entender el MOVIMIENTO de una página (verificado 8-ago-2026 en zero.university)

Caso: el LLM debe "ver" la página y entender las animaciones scroll-driven (parallax, reveals,
transforms). Stack decidido con evidencia:

**Navegador para este caso = agent-browser + ffmpeg** (NO playwright: su `record_video` da
`page.video=None` con Chromium 151 — headless shell y headed — y el screencast CDP no emite
frames; probado). Modelo de visión = qwen/qwen3.8-max vía OpenRouter (acepta imágenes Y vídeo).

Patrón A — frames + descripciones (sin vídeo): `~/.hermes/scripts/scroll_vision.sh <URL> [N] [OUT]`
1. agent-browser: open + viewport 1440x900 + `eval window.scrollTo(0, Y)` por pasos + screenshot por posición
2. `diff screenshot --baseline` entre frames → % de píxeles cambiados por tramo (métrica de movimiento; los elementos sticky aparecen como 0% de cambio)
3. conversión sips→JPEG + descripción por frame con `~/.hermes/scripts/vision_qwen.py` (imagen local → base64 data URL)
4. síntesis del movimiento por secciones. Resultado real: 13 frames de zero.university → 12 secciones descritas (hero escritorio, categorías, campus 3D, retos, portfolio, recruiters, pricing, CTA).

Patrón B — vídeo + Qwen video (mejor para movimiento): `~/.hermes/scripts/scroll_frames_video.sh <URL> [N_FRAMES] [OUT]`
1. 120 screenshots en pasos de scroll (~135px) con wait 120ms → ffmpeg → mp4 h264 de ~8s a 15fps (4.5MB)
2. exponer con túnel: `python3 -m http.server <puerto> --bind 127.0.0.1 --directory <dir>` + `cloudflared tunnel --url http://127.0.0.1:<puerto>` → URL trycloudflare
3. `vision_qwen.py <URL_publica.mp4> "describe el movimiento..."` → usa `{"type":"video_url","video_url":{"url":...}}` (requiere URL pública; el vídeo local NO vale)
4. Resultado real: Qwen describió todo el scroll-telling de zero.university (texto que cambia en el hero, reveals secuenciales, flyover 3D con parallax, cards flotantes, CTA pinned).

## Pitfalls (aprendidos en el spike 8-ago y benchmark moli 13-ago)
- ⚠️ **Chrome de Google se CUELGA en headless CLI** (13-ago-2026, benchmark moli): `Google Chrome --headless=new --dump-dom URL` no termina nunca en este Mac (keystone/updater, incluso con `--user-data-dir` nuevo, headless clásico incluido; >120s sin output). Para automatización CLI usar **chrome-headless-shell** de Playwright cacheado: `~/Library/Caches/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell` (Chromium real sin keystone; example.com en 2.5s). agent-browser no se ve afectado (usa su propio binario).
- ⚠️ **El daemon reutiliza el browser entre invocaciones** (`lifecycle.reused: true`) y el audit
  VARÍA: color-contrast depende del render (0 vs 1+1 violaciones; nodos 10 vs 41). Para audits
  reproducibles: `agent-browser close --all` antes (el wrapper ya lo hace) y, si el resultado
  es borderline, repetir (lección N≥3 del eval clean-transcript).
- ⚠️ **`--json` NO incluye `passes`** como lista: solo `counts.passes` + `violations` +
  `incomplete` (cada violation con `nodes[]` y targets). Estructura: `{"success":true,"data":{...}}`.
- ⚠️ **chat** (control LLM por lenguaje natural) requiere `AI_GATEWAY_API_KEY` (AI Gateway de
  Vercel; modelo por defecto anthropic/claude-sonnet-4.6, configurable con `--model`). Sin esa
  key, usar la navegación determinista + Hermes browser tools.
- ⚠️ **Playwright NO graba vídeo en este entorno**: `record_video` → `page.video=None` con
  Chromium for Testing 151 (headless shell y headed); screencast CDP (Page.startScreencast)
  no emite frames vía playwright. Usar agent-browser+ffmpeg (Patrón B) o puppeteer con el
  chromium completo `--headless=new` (teórico, no probado).
- ⚠️ **Puerto 8899 ocupado por un server Python viejo de Langfuse** (cwd ~/langfuse, Python 3.9
  del CommandLineTools). Usar otro puerto (8898+) para http.server propios.
- ⚠️ **vision_qwen.py**: vídeos requieren URL pública (túnel), no path local; el output de
  qwen3.8-max incluye razonamiento visible antes de la respuesta — pedir "responde directo"
  si se quiere output limpio.
- Clicks fallan temprano si otro elemento cubre el target (banner de consentimiento): dismiss y
  snapshot fresco antes de reintentar.
- `agent-browser read` con URL hace fetch HTTP directo (no usa cookies de sesión): para páginas
  con auth, omitir URL (lee la pestaña activa del browser).
- Safari/iOS WebDriver no soportan a11y: usar Chrome.

## Verificación
- `agent-browser a11y <url> --tags wcag2a,wcag2aa` → counts con violations/passes.
- Benchmark del spike: `~/projects/<bench>/` (flows + audits).
