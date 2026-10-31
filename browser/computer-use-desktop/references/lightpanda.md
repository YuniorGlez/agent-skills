# Lightpanda: navegador headless para agentes (medido 31-oct-2026)

Motor propio en Zig, sin render. 1.0.2, binario 89 MB, sin firmar (adhoc, `spctl` lo rechaza).
No sustituye a un navegador de escritorio: no hay UI ni pestañas visibles, y **no tiene la sesión
del usuario** salvo que se le inyecten cookies.

## Instalación

```bash
curl -sL -o ~/.local/bin/lightpanda \
  https://github.com/lightpanda-io/browser/releases/download/1.0.2/lightpanda-aarch64-macos
chmod +x ~/.local/bin/lightpanda && lightpanda version
```

Comandos: `fetch`, `serve` (CDP), `mcp` (stdio o HTTP), `agent` (agente con LLM, usa OpenAI),
`run` (scripts).

## Con cookies del navegador del usuario: sí funciona (probado 31-oct-2026)

Es la forma de darle sesión. Funciona para X; en LinkedIn solo a medias.

1. **Extraer las cookies del navegador por CDP** (`scripts/cdpx_cookies.js`): conecta a la pestaña,
   `Network.enable` (sin esto `getAllCookies` devuelve vacío), `Network.getAllCookies`, filtra por
   dominio y guarda un array en formato CDP/Puppeteer con modo `0600`. **No imprime valores**, solo
   nombres. Medido: 3.630 cookies en total en Dia, 30 de `linkedin.com`, 87 de `x.com`.
2. **Servirlas a Lightpanda**: `lightpanda serve --port 9223 --cookie <fichero>` (o
   `lightpanda fetch <url> --cookie <fichero>`). El formato se detecta solo (JSON CDP o cookies.txt).
3. **Borrar el fichero al terminar** y parar el proceso: son credenciales de sesión. Comprobar con
   `rg -l "auth_token|li_at"` que no queda rastro.

### Resultados

| Sitio | Sin cookies | Con cookies |
|---|---|---|
| **x.com/home** | 6 KB, sin timeline | **185 posts únicos, 164 cuentas, 23,5 s, 165 MB** (`scripts/lp_xwall.js`) |
| **linkedin.com/feed** | 21 KB, página de login | Logueado: 51 KB de texto, nombre, analytics y página de empresa — **pero 0 publicaciones del muro** |

- X queda resuelto: con `scrollBy` + espera, el mismo muro que costó **100 posts en 97 s con
  agent-desktop sobre la app** sale aquí **185 posts en 23,5 s**, y sin ventana.
- LinkedIn no: su feed usa componentes que el motor no termina de ejecutar. Para LinkedIn sigue
  mandando el navegador real (Dia + CDP).

**Seguridad:** las cookies de sesión son credenciales. No se imprimen, no se copian a un informe, el
fichero va en `0600` y se borra al acabar. No inyectar cookies sin permiso explícito del operador.

## GitHub con Lightpanda: leer sí, buscar solo por CDP (medido 31-oct-2026)

| Tarea | `fetch` | CDP |
|---|---|---|
| Página de un repo, issue o PR | **Sí**: 34.650 bytes de markdown del repo de Lightpanda, 105 MB de pico | Sí |
| Búsqueda (`github.com/search?q=…&type=repositories`) | **No**: devuelve la página sin resultados (se renderiza por JS) | **Sí**: 10 tarjetas por página |

`scripts/gh_search_lp.js --port 9225 --query "topic:ai-agents pushed:>2026-10-16" --pages 2` devuelve
15 repos en 14 s con 91 MB: nombre, descripción, lenguaje, estrellas y «Updated hace N segundos».

**Verificado contra la API**: los cuatro primeros repos del scraping (`fastagent-sh/fastagent` ★65,
`lehard/dev-platform` ★0, `gustmrg/wisp-bot` ★0, `mknw/hames-playground` ★3) coinciden con
`gh api repos/<name>` en estrellas y `pushed_at` del mismo día.

**Cuándo cada una**: para buscar repos, `gh api search/repositories` es superior — JSON exacto,
`total_count` (38.277 con ese filtro), paginación de 100 y filtros de fecha (`pushed:` actividad,
`created:` novedad). Lightpanda sirve de respaldo sin token y para **leer** páginas de GitHub sin gastar
rate limit. Ojo: sin sesión, GitHub muestra «Sign in» en el HTML; el contenido público se lee igual.

## Cuándo usarlo (y cuándo no)

| Tarea | Lightpanda | Alternativa |
|---|---|---|
| Leer muchas páginas públicas en paralelo | **Sí** — 8 páginas en 3,2 s con 175 MB de pico | Chrome: >1 GB |
| Extraer texto/markdown de artículos, docs, listados | **Sí**, y con `--dump markdown` sale limpio | — |
| Web con sesión (LinkedIn, Gmail, Discord, X) | **No** sin cookies; con `--cookie` es posible pero frágil | navegador del usuario + CDP |
| Web con anti-bot o JS de render (Booking) | **No**: devuelve 0 bytes y sale con código 0 | Chrome |
| Verificar píxeles, animaciones, layout | **No**: no renderiza | captura real |

## Trampa: `fetch --dump markdown` pierde las SPA

En una home Next con animaciones (GSAP), `fetch --dump markdown` devolvió **47 bytes** mientras por
CDP el mismo sitio exponía 1.408 nodos y 9.618 caracteres de texto. El motor ejecuta JS; el dump no
espera a todo. Para SPAs, ir por CDP y leer `document.body.innerText`.

Segunda trampa: `fetch` puede devolver **0 bytes con exit 0** (Booking). Un cero silencioso no es
«página vacía»: es bloqueo. Comprobar siempre el tamaño de la salida.

## CDP: compatible, con diferencias

- `GET /json/version` responde (`Browser: Lightpanda/1.0`, protocol 1.3).
- **`/json/list` está vacío y `PUT /json/new` devuelve `Not found`.** No se pueden usar los scripts
  basados en listar pestañas.
- Hay que crear el target por websocket:
  `Target.createTarget({url})` → `Target.attachToTarget({targetId, flatten:true})` → `Runtime.evaluate`
  con el `sessionId`. Ver `scripts/lp_cdp.js`.
- `Target.createTarget` sobre la misma conexión devuelve `TargetAlreadyLoaded` si repites URL: una
  conexión (websocket) por página. Con 8 conexiones simultáneas funcionó 8/8.
- RAM del servidor: 18–28 MB en reposo; 175 MB con 8 páginas cargadas.

## Coste medido por página (fetch, una pasada)

| Sitio | Lightpanda (s / MB / bytes) | Chrome headless (s / MB / bytes) |
|---|---|---|
| example.com | 0,42 / 30,5 / 1.344 | 0,62 / 91,1 / 2.375 |
| Hacker News | 1,30 / 31,2 / 19.230 | 1,19 / 94,5 / 34.516 |
| la agencia.com (SPA) | 0,71 / 42,8 / 47 | 1,53 / 212,5 / 127.167 |
| informe Next | 0,47 / 28,6 / 7.400 | 0,42 / 103,8 / 14.792 |
| booking.com | 0,85 / 50,8 / **0** | 7,64 / 307,0 / 647.933 |
| linkedin.com | 0,98 / 62,6 / 21.625 | 6,07 / 286,1 / 159.555 |
| x.com (perfil) | 2,62 / 99,7 / 6.281 | 0,52 / 86,8 / **40** |

Memoria: 2–5× menos en casi todo. Velocidad: parecida en webs ligeras, 6–9× más rápido en webs
pesadas (pero devolviendo menos contenido). Donde Chrome devuelve 40 bytes y Lightpanda 6 KB, gana
Lightpanda por anti-bot, no por velocidad.

## MCP

`lightpanda mcp` arranca un servidor MCP por stdio o HTTP (`--port`), con sesión de navegador
independiente por cliente, y puede exponer CDP a la vez (`--cdp-port`, no combinable con `--port`).
Es la vía limpia para dárselo a un agente sin escribir un cliente CDP.

## Privacidad

Los modos `fetch`, `serve` y `mcp` no hablan con terceros (los dominios del binario son specs
w3.org/unicode.org, github, localhost y la fuente DejaVu). El comando `agent` sí usa un proveedor
(auth.openai.com aparece en el binario): no usarlo con contenido sensible sin revisar la configuración.

## Scripts

- `scripts/lp_cdp.js --port 9223 --url <url> --js "…" [--wait ms]` — target + session + evaluate.
- `scripts/lp_xwall.js --port 9223 --iters 6` — muro de X con scroll y dedupe (requiere cookies).
- `scripts/cdpx_cookies.js --port 9222 --match <url> --domain <dom> --out <ruta>` — exporta cookies
  del navegador por CDP sin imprimir valores.
- `scripts/lp_parallel.js` — N conexiones en paralelo para medir concurrencia y RAM.
- `scripts/lp_bench.py` — comparativa Lightpanda vs Chrome headless por URL.
