---
name: accesibilidad-wcag
description: "Auditar y corregir accesibilidad web WCAG 2.2 AA."
version: 1.0.0
author: Hermes + el operador
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [a11y, wcag, accesibilidad, axe, contraste, teclado, wcag22]
---

# Accesibilidad web (WCAG 2.2 AA) — auditar, corregir y demostrarlo

## When to Use

- El usuario pide «que la web sea accesible», revisa accesibilidad, cita WCAG 2.2 / RD 1112/2018 / EN 301549.
- Llega un documento con recomendaciones de accesibilidad (de un cliente, una compañera, un pliego) y hay que
aplicarlas y reportar.
- Se toca un mapa, un formulario, un asistente de voz, tablas o vídeo y se quiere saber si sigue siendo usable.
- Antes de entregar cualquier interfaz a un cliente del sector público.

Sirve para cualquier web o app (Next, Vite, HTML suelto). El entregable no es «he mirado cosas»: es
**0 violaciones con evidencia medible** y un informe con el porqué de cada cambio.

## Orden de trabajo

1. **Línea base, antes de tocar nada.** Auditoría automática en TODAS las rutas (públicas y con sesión).
   Guarda el JSON: es la prueba del antes.
2. **Corregir por familias**, no por hallazgo: tokens de contraste, foco, formularios, tablas, mapa, vídeo.
3. **Verificar con tres herramientas distintas** (la automática sola no vale).
4. **Si hay despliegue, repite la auditoría contra la URL PUBLICADA**, no contra local: axe sobre la portada
y la declaración, la declaración accesible sin cookie (200, no 307) y el MIME de los ficheros nuevos
(un `.vtt` que no llegue como `text/vtt` no carga aunque exista).
5. **Informe** con: punto del requisito → cambio → fichero → por qué, y la tabla de resultados.

## Herramientas (verificadas)

```bash
# 1. axe-core nativo, sin escribir código (agent-browser CLI)
agent-browser a11y <url> --tags wcag2a,wcag2aa            # legible
agent-browser a11y <url> --tags wcag2a,wcag2aa --json     # estructurado (counts/incomplete/violations)
```

Para rutas con login, el login por `eval` **no es fiable**: hay que esperar de verdad a que la página
cargue antes del `fetch` (un `agent-browser wait <ms>` no basta; usa `sleep 3` y reintenta hasta ver un
`200`). Comprueba que sigues autenticado en cada ruta (busca un landmark de la app, p. ej. `aside`), o
estarás auditando la pantalla de login creyendo que auditas la app. Encadenar muchas órdenes `a11y` puede
dejar la ventana sin cookies: vuelve a entrar antes de cada tanda en vez de fiarte de la primera pasada.
Lote completo de rutas con axe, en un solo comando: `scripts/audit-axe.sh` (más abajo).

```bash
# 2. Contraste MEDIDO de todo el texto (Playwright + cálculo propio)
NODE_PATH=$(npm root -g) node scripts/contrast-check.mjs <url> <clave>
# 3. Teclado, móvil, texto al 200 %, movimiento reducido
NODE_PATH=$(npm root -g) node scripts/a11y-check.mjs <url> <clave>
```

Plantillas listas para copiar: `references/contrast-check.mjs` y `references/a11y-check.mjs`. **Los scripts
con `import`/`require('playwright')` tienen que estar DENTRO del proyecto**: `NODE_PATH` no funciona con
ESM y el `require` se resuelve desde el directorio del script.

## Qué corrige de verdad (por orden de impacto)

- **Contraste**: el token de texto secundario suele fallar (4,24:1 sobre fondo claro y ~3,9:1 sobre fondos
tintados). No cambies la paleta: añade un token de tinta (`--slate-ink`) del mismo tono, oscurecido lo
justo, y mapea la utilidad de texto a él. Lo mismo con los tonos de aviso dentro de chips.
- **Foco**: regla global `:where(a, button, input, select, textarea, summary, [tabindex]):focus-visible`
(muchos proyectos solo la tienen en `a`, `.btn` e `.input`). Añade `scroll-padding-top` para que los saltos
de ancla no dejen el título bajo una barra pegajosa.
- **Enlaces dentro de párrafos**: subrayado por defecto (`a { text-decoration: underline }`) y `no-underline`
en los que funcionan como botón. Sin eso, axe da `link-in-text-block`.
- **Regiones desplazables**: todo `overflow-x: auto` (tablas, bloques de código) necesita `tabindex="0"` y
un nombre (`role="region"` + `aria-label`), o axe da `scrollable-region-focusable`.
- **`aria-label` en `<div>`/`<span>` sin rol** → axe `aria-prohibited-attr`: añade `role="group"`/
`role="list"` o sustituye por texto real (`.sr-only`).
- **Tablas**: `<caption>` (aunque sea `sr-only`) y `scope="col"`/`scope="row"`. Los gráficos de barras
CSS se convierten en tabla con la barra `aria-hidden` y el número en texto.
- **Formularios**: etiqueta visible con `htmlFor`, `required` en el campo, `aria-describedby` al mensaje y
`role="alert"` para errores / `role="status"` para confirmaciones. Nunca `placeholder` como etiqueta.
- **Color como único canal**: añade un segundo canal (tamaño/forma/patrón) **y** el dato en texto en la
leyenda/tabla. Es más barato y más honesto que pelear con el renderer del mapa.
- **Vídeo**: `<track kind="captions">` + transcripción en texto (WCAG 1.2.2 y 1.2.1). Los tiempos de los
subtítulos tienen que salir de transcribir el audio REAL (`whisper small` en local), no del guion: el MP4
publicado suele ser otra versión y los tiempos no cuadran.
- **Mapas con canvas**: canvas enfocable + `aria-describedby` con instrucciones y **alternativa textual
completa** (tabla con enlaces a las fichas). No luches por hacer enfocables los marcadores; MapLibre ya
etiqueta el lienzo solo (locale `Map.Title`).
- **Declaración de accesibilidad**: página pública (ruta abierta en el middleware) con estado, hecho,
limitaciones conocidas, cómo se ha comprobado y cómo reportar. Sin prometer conformidad legal.

## Pitfalls (caros, ya pagados)

- **axe deja en `incomplete` lo que no puede resolver** (texto encima de un SVG, de un gradiente o
  solapado por una caja). Eso no es «pasa»: mídelo con `contrast-check.mjs`, que sube por el árbol
  componiendo la opacidad de los ancestros. Y no borres los `incomplete` del informe: se explican.
- **Cambiar el texto de una etiqueta cambia el nombre accesible del campo.** Meter «(obligatorio)» dentro
del `<label>` rompe los e2e que buscan `getByLabel("Email")`. Patrón correcto: asterisco con
`aria-hidden="true"` + nota «Los campos marcados con * son obligatorios» + `required` en el campo.
- **Texto al 200 % (zoom solo-texto): un contenedor `flex` con `flex-wrap` y altura fija (p. ej. `h-screen`)
reparte sus hijos en VARIAS COLUMNAS** y se salen de la pantalla. Se ve en la barra lateral y en el menú.
Arreglo: `md:flex-nowrap` en el contenedor + una sola columna con `overflow-y: auto` y `min-h-0`.
- **Los `rem` de las media queries se evalúan con el tamaño de fuente inicial**, así que el layout NO cambia
de breakpoint al subir `html { font-size: 200% }`; lo que se rompe es la distribución interna.
- **Un parche (patch) sobre un template literal con barras invertidas** puede duplicarlas o convertirlas en
un `\n` literal. Verifica después con `repr()` en Python, no a ojo.
- **Al 200 % de texto la barra de navegación de una landing se sale** en 320 px: deja que haga `flex-wrap`
(`@media (max-width: 400px) { .nav-in { flex-wrap: wrap; height: auto } }`).
- **`window.resizeTo` no sirve para probar móvil** con una sesión de navegador ya lanzada: usa Playwright
con `newContext({ viewport })`.
- Si el proyecto está i18n-izado, **toda cadena nueva tiene que existir en el idioma base y traducirse a
los demás** antes de dar por cerrado (`bun run i18n:check` suele delatarlo).
- **La declaración de accesibilidad tiene que quedar FUERA del muro de sesión.** Si el middleware la
redirige a `/login`, no cumple. Añádela a las rutas públicas del proxy/middleware y compruébalo con `curl`
**sin cookie** (200, no 307): una auditoría hecha con sesión no detecta este fallo.
- **Un fichero nuevo en `public/` puede servirse con el MIME equivocado y la función muere en silencio.**
Sin `Content-Type: text/vtt` el navegador no carga los subtítulos. Comprueba
`curl -s -o /dev/null -w '%{content_type}' <url>` de cada asset nuevo, no solo que devuelva 200.
- Si hay e2e propios, **ejecútalos al final**: son la red que detecta la regresión que tú no ves.

## Cómo se demuestra (tabla del informe)

| Comprobación | Evidencia |
|---|---|
| axe-core, todas las rutas | 0 violaciones + nº de `passes` (antes/después) |
| Contraste | nº de elementos de texto medidos y nº de fallos |
| Teclado, móvil, texto al 200 % | 0 desbordes y primer tabulador = enlace de salto |
| Regresión | tests del proyecto en verde + typecheck |

## Referencias

- `scripts/audit-axe.sh` — lote de axe-core por todas las rutas (con login opcional) y resumen por ruta.
- `references/contrast-check.mjs` — contraste medido de todo el texto visible (Playwright).
- `references/a11y-check.mjs` — teclado, móvil, 200 %, tabla alternativa, movimiento reducido.
- `references/informe-accesibilidad-gcn.md` — ejemplo real de informe (Green Corridors Navigator, oct-2026).
