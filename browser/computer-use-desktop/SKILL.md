---
name: computer-use-desktop
description: "Use when a task needs desktop computer use (GUI apps)."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [computer-use, desktop, macos, accessibility, cua-driver, agent-desktop]
    category: devops
    related_skills: [chrome-cdp-access, agent-browser, third-party-repo-triage]
---

# Computer use de escritorio (macOS)

## When to Use

Cuando la tarea pide operar **apps de escritorio** en vez de una web: abrir una app y mandarle una tarea,
pulsar botones, escribir en un campo, hacer scroll y leer, mandar un prompt a una app de escritorio, o
comprobar si un agente puede manejar la pantalla. También cuando una herramienta de computer use empieza a
devolver errores raros de ventanas: se empieza siempre por los prechecks de § 1.

Cubre la elección de herramienta, los prechecks que evitan media hora de diagnóstico falso, y los pitfalls
que hacen que el árbol de accesibilidad parezca roto cuando no lo está.

## 1 · Prechecks obligatorios (antes de la primera llamada)

1. **La pantalla tiene que estar desbloqueada.** Es lo primero, antes de instalar, configurar o depurar:
   ```bash
   python3 scripts/session-lock-check.py     # LOCKED / UNLOCKED + segundos de inactividad
   ```
   Con `CGSSessionScreenIsLocked = 1` el proceso en primer plano es `loginwindow`, ninguna app expone su
   ventana y **todas** las herramientas fallan con errores que parecen bugs propios: «window exists but is
   not exposed through accessibility», `frontmost_window_join`, `0 elements`, `TIMEOUT` del inventario
   global. Dos herramientas independientes fallando igual es la señal de que el problema es la sesión, no
   la app.
2. **Permisos TCC del proceso que lanza**, no de la shell. Accesibilidad es obligatoria; grabación de
   pantalla solo para capturas; automatización solo para quien maneje System Events.
   Ojo: un `status` que dice `accessibility: granted` **no prueba** que el árbol se pueda leer — comprueba el
   grant, no el resultado. La prueba real es una sonda directa (`scripts/ax-probe.py`) o un `snapshot` que
   devuelva árbol.
3. **¿Hay alguien delante del Mac?** `HIDIdleTime` de horas + `lsappinfo front` → `loginwindow` significa que
   el usuario no está: no insistir, decir qué falta y parar. Los tests de GUI se hacen cuando vuelva.

## 2 · Elegir la vía (no todas sirven para lo mismo)

| Tarea | Herramienta | Por qué |
|---|---|---|
| Operar cualquier app GUI por semántica | **agent-desktop** (ver `references/agent-desktop.md`) | Devuelve una `ref` estable por elemento, va headless por defecto y dice si la acción se entregó |
| Leer canales o hilos de Discord de escritorio | agent-desktop + `references/discord-desktop.md` | El árbol trae canales, hilos y mensajes completos; `scroll-to` carga historial |
| Operar Dia (navegador) | **No por accesibilidad** — CDP con `--remote-debugging-port=9222` (ver `references/dia-browser.md`) | Su renderer no activa la accesibilidad ni con `--force-renderer-accessibility`; CDP sí funciona |
| Publicar o dejar en borrador en LinkedIn | CDP sobre Dia + `references/linkedin-compose.md` | Composer propio, borrador guardado y verificado; programar no existe en perfil personal |
| Recetas de apps ya probadas (Calculadora, TextEdit, X, Discord, Claude) | `references/apps-recipes.md` | Nombres reales, coste en tokens y qué acción funciona en cada una |
| Captura visual y clic por índice, ya integrado en Hermes | **`computer_use`** (cua-driver) | Entrada en segundo plano sin robar foco; `list_windows` da z-index y `off_screen` |
| Navegador, sesión del usuario, DOM o JS | **CDP o Playwright** (skill `chrome-cdp-access`) | No gastar computer use en lo web: el DOM es más barato y más fiable |
| App sin árbol de accesibilidad (juegos, lienzos, Dia) | Captura + coordenadas | Es el único camino; asumir que no hay verificación semántica |
| Leer muchas páginas públicas sin sesión, en paralelo | **Lightpanda** (`references/lightpanda.md`) | 8 páginas en 3,2 s y 175 MB; no sirve para webs con login ni anti-bot |

## 3 · El loop (observar → actuar → verificar)

Ninguna de estas herramientas es un agente: devuelven estado y ejecutan una acción; el bucle lo pone quien
las llama. La forma correcta, en agent-desktop:

```
agent-desktop snapshot --skeleton --app "App" -i --compact   # mapa superficial, children_count en las ramas cortadas
agent-desktop snapshot --root @s8f3k2p9:e3 -i --compact      # bajar a una sola región
agent-desktop click @s8f3k2p9:e12                             # actuar sobre una ref cualificada
agent-desktop snapshot --root @s8f3k2p9:e3 -i --compact      # verificar: releer la misma región
```

- **Las refs valen para un snapshot.** Ante `STALE_REF`, `AMBIGUOUS_TARGET` o `SNAPSHOT_NOT_FOUND` se toma
  uno nuevo; no se reintenta la misma ref.
- **Reintentar solo si `disposition.retry` es `safe`** (normalmente `not_delivered`). Cualquier otra entrega
  significa que la acción pudo llegar: un segundo clic duplica, y `toggle` se deshace a sí mismo.
- **No fiarse del `ok`**: comprobar con una lectura posterior (`get`, `is` o snapshot nuevo). Finder devuelve
  éxito de un `AXConfirm` que no hace nada.
- **Nunca esperar con un sleep fijo** donde haya un `wait` propio.

## 4 · Reglas de seguridad

- **Headless por defecto** (sin mover el cursor ni robar foco). `--headed` solo si el usuario lo autoriza de
  forma explícita: es visible en su pantalla y puede pisar lo que esté haciendo.
- **Nunca teclear contraseñas, códigos 2FA ni datos de tarjeta**, ni siquiera si el usuario los pega en el chat.
  Si hace falta un login, que lo haga él y seguir después.
- **Leer antes de tocar:** no cerrar apps del usuario, no escribir en documentos reales, no mandar mensajes
  desde su cuenta sin permiso. Para pruebas, apps neutras (Calculadora, TextEdit con documento nuevo) y cerrar
  sin guardar (`close-app --force`).
- **Los snapshots contienen texto de la pantalla.** Guardarlos en un directorio de scratch, nunca en registros
  públicos ni en un informe.

## 5 · Pitfalls

- **Nombres de app LOCALIZADOS.** `launch "Calculator"` abre «Calculadora»; luego `--app "Calculator"` da
  `APP_NOT_FOUND` porque el nombre resuelto es el del sistema. Igual con TextEdit → «Editor de Texto».
  Lanzar con el nombre en inglés y capturar con el nombre que devuelve `launch`. Verificar con `list-apps`.
- **`type` falla en composers `contenteditable`** (Claude Desktop, muchas apps Electron): la acción se
  entrega por `AXSelectedText` pero el campo queda vacío (`value: "\n"`) y el texto no aparece. Lo que sí
  funciona: `set-value <ref> "texto"` (devuelve `delivered_verified` y el valor se lee con `get`) o
  `--headed type`. En Claude Desktop, tras escribir, el envío necesita `--headed press return`; se confirma
  cuando el composer se vacía y aparece «Dijiste: …» en el hilo.
- **`scroll` miente en el `ok`, no en el efecto.** Sobre el `scrollarea` de una SPA devuelve
  `ACTION_FAILED` y **sí desplaza** (25/25 veces, medido leyendo posts nuevos después). No reintentar a
  ciegas: verificar por observación (contenido nuevo) y seguir. `scroll` sobre un `article` da `STALE_REF`
  porque la lista virtualiza; hay que usar el `scrollarea` y refrescar su ref en cada iteración.
- **`--skeleton` en Electron/Chromium puede devolver un mapa vacío** (nodos sin `children_count`, 1 ref) y
  el snapshot **completo** de la misma app devuelve 204 refs. Si el esqueleto no trae cortes, no insistas:
  pide el árbol completo, acepta el coste y filtra en código.
- **`osascript … count windows` devuelve 0 en silencio** cuando el proceso llamante no tiene accesibilidad (no
  lanza -1743). No usar ese 0 como prueba de que la app no tiene ventanas: contrastarlo con una sonda directa
  a `AXWindows` (ctypes), que sí da el número real.
- **El inventario global es la pieza frágil** de agent-desktop: una entrada obsoleta de una app, una app cuyo
  `launchDate` no cuadra con el arranque del proceso, o una ventana en **otro Space** tumba `list-windows`,
  `focus-window` y `snapshot` sin app. `list-apps --app X` y `snapshot --app X` siguen funcionando: si un
  comando global falla y el específico no, es esto y no los permisos.
- **Apps densas (Chromium, Electron, tablas largas):** `--skeleton -i --compact` y luego `--root @ref`. Un
  snapshot completo de una tabla larga puede tardar decenas de segundos y devolver miles de refs.
- **`launch` no siempre trae la app al frente.** Si necesitas foco, `--activate`; si aun así no, es que la
  ventana está en otro Space o la sesión está bloqueada.
- **Binarios de terceros adhoc/no notarizados:** firmar con `codesign` no es obligatorio para que funcionen
  desde terminal, pero `spctl` los rechaza. Decirlo en el informe en vez de dar por hecho que están firmados.
- **Un paquete con `postinstall` bloqueado por bun queda en modo wrapper** y paga ~125 ms por llamada. Si se
  autoriza (`--trust`), leer antes el script: aprobarlo es ejecutar código de terceros.

## Soporte

- `scripts/session-lock-check.py` — ¿está bloqueada la pantalla? (ctypes + CoreGraphics, sin dependencias).
- `scripts/ax-probe.py` — sonda directa al árbol de accesibilidad de un pid: `AXIsProcessTrusted()` y cuántas
  ventanas ve. Distingue «sin permisos» de «sin ventanas» de «sesión bloqueada».
- `scripts/ax-force-a11y.py <pid>` — intenta activar `AXManualAccessibility` como VoiceOver. Devuelve el
  código de error; sirve para demostrar que un renderer (Dia) no responde aunque el grant exista.
- `scripts/discord_read.py list | read <canal> [n] | tour a,b,c` — canales y mensajes de Discord.app.
- `scripts/discord_deep.py <canal> [iteraciones]` — historial hacia arriba con `scroll-to`.
- `scripts/tw100.py [objetivo] [iteraciones]` — scroll y lectura de N posts del muro de X con dedupe.
- `references/agent-desktop.md` — ficha de la herramienta: instalación y verificación, grupos de comandos,
  contrato JSON, códigos de error y `disposition`, latencias medidas y puntos frágiles.
- `references/apps-recipes.md` — qué funciona en cada app probada y coste en tokens.
- `references/discord-desktop.md` — estructura del árbol de Discord, `scroll-to` para historial, reglas.
- `references/dia-browser.md` — por qué Dia no se puede controlar por accesibilidad y qué alternativas hay.
- `references/linkedin-compose.md` — navegar LinkedIn y dejar un post en borrador con CDP (verificado).
- `references/lightpanda.md` — navegador headless en Zig: cuándo gana a Chromium, diferencias de CDP y coste medido.

## Lo que cuesta de verdad (medido 31-oct-2026, macOS 27.0.1 arm64)

Latencias medias de 5 llamadas en caliente sobre una app pequeña:

| Comando | ms |
|---|---|
| `get` / `is` | 115–118 |
| `list-windows --app` | 155 |
| `list-windows` global | 195 |
| `snapshot --compact` | 238 |
| `click` | 250 |
| `status` | 129 |
| `list-apps` | 206 |

Coste en contexto, que es lo que decide si un bucle es viable:

| Caso | refs | ≈tokens |
|---|---|---|
| Chrome `--skeleton` | 19 | 1.366 |
| Chrome completo | 50 | 3.673 |
| X (Twitter.app) `--skeleton` | 10 | 470 |
| X completo (timeline) | 150 | 11.526 |

El esqueleto cuesta 4–24× menos, pero no permite actuar: hay que bajar con `--root`. Leer 100 posts de X
con scroll incremental costó 26 snapshots, 2,4 MB leídos y 97 s.

**Multi-agente sobre una app**: dos `session start` + `snapshot` simultáneos funcionan (321 y 340 ms, 27 refs
cada uno, `snapshot_id` distintos) y una ref de la sesión A usada desde la B da `SNAPSHOT_NOT_FOUND`. El
claim «many agents on one app at once» se sostiene, con refs namespaced por sesión.

**Cerrar apps de prueba**: `close-app "App"` devuelve `delivered_verified` con evidencia
`process_instance_exited`; `cmd+w` por `press` no cierra el documento (queda `delivered_unverified`).
