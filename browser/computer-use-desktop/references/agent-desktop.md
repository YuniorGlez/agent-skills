# agent-desktop (vercel-labs) — ficha de la herramienta

CLI en Rust (más librería C) que expone el árbol de accesibilidad del sistema como JSON con una `ref` por
elemento accionable. No es un agente: devuelve estado y ejecuta acciones; el bucle observe→act→verify lo pone
quien lo llama. Apache-2.0, sin dependencias npm, binarios precompilados por plataforma con su `.sha256`.

## Instalación y verificación

```bash
bun add -g agent-desktop --trust      # bun bloquea el postinstall por defecto
agent-desktop version                 # {"os":"macos","target":"aarch64","version":"…"}
agent-desktop status                  # permisos + superficies soportadas + raíz de estado
agent-desktop skills get desktop      # el contrato que trae el propio binario (autoritativo para su versión)
agent-desktop skills get platform     # lo que cambia en este OS
```

Sin el postinstall, el `bin` queda como wrapper de Node y avisa de ~125 ms extra por llamada; el paquete
sigue funcionando, pero conviene enlazarlo al binario nativo.

Estado en `~/.agent-desktop` (relocalizable con `AGENT_DESKTOP_HOME`). No crea LaunchAgents. Mantiene un
proceso host privado por namespace de snapshot, ~15 MB RSS, que muere a los 15 minutos de inactividad.
Desinstalar: `bun remove -g agent-desktop`.

## Contrato de salida

Un único envelope por comando:

```json
{"version":"2.5","ok":true,"command":"snapshot","data":{…}}
{"version":"2.5","ok":false,"command":"click","error":{"code":"STALE_REF","message":"…",
 "suggestion":"…","disposition":{"delivery":"not_delivered","retry":"safe"}}}
```

- Códigos: `PERM_DENIED`, `ELEMENT_NOT_FOUND`, `APP_NOT_FOUND`, `ACTION_FAILED`, `ACTION_NOT_SUPPORTED`,
  `STALE_REF`, `AMBIGUOUS_TARGET`, `WINDOW_NOT_FOUND`, `TIMEOUT`, `INVALID_ARGS`, `POLICY_DENIED`,
  `APP_UNRESPONSIVE`, `NOTIFICATION_NOT_FOUND`, `SNAPSHOT_NOT_FOUND`, `INTERNAL`.
- Salidas: 0 éxito, 1 error estructurado, 2 argumentos. Ramificar por `code` y `disposition`, nunca por el
  texto de `message` (cambia entre versiones).
- `delivery`: `delivered_verified` (hay lectura posterior), `delivered_unverified` (dispatch sin lectura),
  `not_delivered` (solo cuando ya se observó que el estado era el pedido). Solo se reintenta lo `safe`.

## Comandos por grupo (60 nombres, 56 operativos en macOS)

| Grupo | Comandos |
|---|---|
| Observar | `snapshot`, `find`, `get`, `is`, `screenshot`, `list-surfaces` |
| Actuar sobre ref | `click`, `double-click`, `triple-click`, `right-click`, `type`, `set-value`, `clear`, `focus`, `select`, `toggle`, `check`, `uncheck`, `expand`, `collapse`, `scroll`, `scroll-to` |
| Teclado y ratón | `press`, `hover`, `drag`, `mouse-move`, `mouse-click`, `mouse-wheel` |
| Apps y ventanas | `launch`, `close-app`, `list-apps`, `list-windows`, `list-displays`, `focus-window`, `resize-window`, `move-window`, `minimize`, `maximize`, `restore` |
| Notificaciones | `list-notifications`, `dismiss-notification`, `dismiss-all-notifications`, `notification-action` |
| Portapapeles | `clipboard-get`, `clipboard-set`, `clipboard-clear` |
| Lote y sistema | `batch`, `session`, `trace`, `cursor-overlay`, `status`, `permissions`, `version`, `skills`, `wait` |

`batch` es secuencial y no atómico: 64 entradas, 1 MB de entrada, 4 MB de salida; valida los nombres de
argumento contra el comando real (`ref_id`, no `ref`) y falla entero si una entrada no valida.

## Semántica de refs

- Formato cualificado `@<snapshot_id>:eN`. Una ref desnuda (`@e1`) se rechaza con `INVALID_ARGS`.
- Solo reciben ref los roles interactivos y los que anuncian acción primaria; el texto estático no.
- La reidentificación usa pid, rol, ruta, superficie, texto estable y hash de bounds; los valores de control
  son volátiles y no identifican. Varios candidatos vivos → `AMBIGUOUS_TARGET`.
- `--skeleton` corta ramas y anota `children_count`; `--root @ref` baja a una región concreta.

## Latencias medidas (arm64, en caliente, sin ventana que leer)

| Comando | Media |
|---|---|
| `version` | ~100 ms |
| `status` | ~130 ms |
| `list-displays` | ~100 ms |
| `list-apps` (72 apps) | ~205 ms |
| `batch` de 2 comandos | ~10 ms |

Sirven de línea base: con la sesión operativa, un `snapshot` de app pequeña debería quedar en el mismo
orden de magnitud; muy por encima indica árbol denso (usar `--skeleton`/`--root`) o app lenta.

## Puntos frágiles conocidos

- **El inventario global** (`list-windows` sin `--app`, `snapshot` sin app, `focus-window`) exige unir la app
  en primer plano con una ventana exacta. Si el frente es `loginwindow` (pantalla bloqueada), no hay ventana
  y devuelve `TIMEOUT`/`global_window_inventory_unstable` con `frontmost_window_join`, sin importar
  `--timeout-ms`. Los comandos por app siguen funcionando.
- **Ventanas en otro Space** no aparecen en el inventario y no se pueden apuntar; conmutar de escritorio las
  recupera.
- **Apps con `launchDate` desalineado** del arranque del proceso tumban el inventario de esa app.
- **`screenshot` necesita grabación de pantalla**; sin ese permiso, `status` lo marca y la captura falla — el
  resto del CLI funciona.
- **Apps Chromium/Electron** activan la accesibilidad web del renderer; tras el primer acceso puede hacer
  falta un snapshot nuevo para que el árbol aparezca completo.

## Seguridad del binario (lo que hay que decir en un informe)

- Firma adhoc/linker-signed sin TeamIdentifier; `spctl -a` lo rechaza (no notarizado). Funciona desde terminal
  porque llega sin cuarentena; la confianza viene del registro npm y del org del repo.
- Sin telemetría en el binario: los dominios que aparecen son el `w3.org` de los SVG, `127.0.0.1` para CDP y
  los endpoints del helper JEV opcional, que envía descripciones de pantalla a un modelo **solo si se invoca**.
- En ejecución: 0 conexiones, 0 puertos a la escucha, un proceso host efímero.
