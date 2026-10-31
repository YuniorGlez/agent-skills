# Recetas por app (medidas, macOS 27)

Cada app expone una parte distinta de su UI por accesibilidad. Lo que sigue son las que se han
probado de verdad y el camino que funcionó. Se ordena por «qué hacer cuando el árbol no responde».

## Regla general

1. `list-windows --app` antes de capturar: si la app tiene 0 ventanas, no es un fallo de permisos.
2. Captura con `-i --compact`. Si trae menos de 5 referencias, pide el árbol completo **sin** `-i`:
   muchas apps Electron no etiquetan lo interactivo y `-i` deja el árbol vacío.
3. Para leer texto de una lista virtualizada (X, Discord, Slack), el dato está en el `description`
   del contenedor de cada fila, no en sus hijos `statictext`.

## Apps probadas

| App | Nombre real del proceso | Captura | Notas |
|---|---|---|---|
| Calculadora | `Calculadora` | 26 refs, 4,6 KB | Botones con nombre semántico: «Multiplicar», «Es igual a», «Borrar todo». El display es `statictext` solo visible sin `-i`. |
| Editor de Texto | `Editor de Texto` | 25–138 refs | Al abrirlo sale el diálogo «Abrir»; el botón «Nuevo documento» crea uno. El cuerpo es un `textfield` que acepta `type` con acentos. |
| X (app Pake) | `Twitter` | 10 refs (esqueleto) / 150 (timeline) | Timeline con `article`; scroll con `scroll` sobre el `scrollarea` (devuelve `ACTION_FAILED` y desplaza). |
| Discord | `Discord` | 143–191 refs, 62 KB | Canales como `link`; mensajes como `article` con `description` ya compuesto. Historial con `scroll-to` sobre el primer `article`. |
| Claude Desktop | `Claude` | 1 ref (esqueleto) / 204 (completo) | `--skeleton` inútil aquí. Composer `contenteditable`: `type` no entra, `set-value` sí. Enviar con `--headed press return`. |
| Dia | `Dia` | **ninguna** | «Renderer did not enable accessibility activation». Ver `dia-browser.md`. |

## Escritura: `type`, `set-value` o `--headed`

- `type <ref> "texto"` funciona en campos nativos (TextEdit: `delivered_verified`, acentos intactos).
- En un `contenteditable` (composers de apps Electron) `type` se marca entregado por `AXSelectedText`
  pero el campo queda en `"\n"` y el texto no aparece. Ahí: `set-value <ref> "texto"`.
- `set-value` escribe el atributo `AXValue`; si la app no reacciona al cambio (React no ve el evento),
  el único camino es `--headed type`, que manda teclado físico al campo enfocado.
- Verificación: `get <ref> --property value`. No te fíes de `delivered_verified` sin leer.

## Desplazamiento: `scroll` vs `scroll-to`

- `scroll <ref> --direction down --amount N` necesita que el elemento anuncie la acción `Scroll`.
  Cuando la anuncia (X, con `scrollarea`), puede devolver `ACTION_FAILED` **y desplazar igual**:
  se comprueba leyendo contenido nuevo, nunca por el `ok`.
- Si el contenedor no anuncia `Scroll` (Discord: `list` de mensajes), `scroll` da
  `ACTION_NOT_SUPPORTED` con `supported_action`. La solución es `scroll-to <primer elemento visible>`,
  que hace `AXScrollToVisible` y devuelve `delivered_verified`; en listas virtualizadas dispara la
  carga de más contenido.
- `scroll` sobre un `article` da `STALE_REF`: la lista virtualiza y las refs cambian.

## Cerrar y verificar

- `close-app "App" --force` devuelve `delivered_verified` con `evidence: process_instance_exited`.
- `cmd+w` por `press` no cierra el documento y queda en `delivered_unverified`.
- Antes de cerrar: comprobar que la app la abriste tú y que no hay documentos sin guardar del usuario.

## Coste de referencia

| Caso | ≈ tokens |
|---|---|
| App pequeña, `-i --compact` | 1.100 |
| X esqueleto / completo | 470 / 11.526 |
| Discord canal, `-i --compact` | 15.000 |
| Claude Desktop completo | 19.000 |

Con esos números, un bucle de 20 capturas sobre Discord cuesta ~300.000 tokens de contexto: hay que
filtrar en código y quedarse solo con los campos que importan.
