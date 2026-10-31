# LinkedIn: navegar y dejar un post en borrador

Medido el 31-oct-2026 en la cuenta de el operador, navegador del usuario (Dia) con CDP.

## Cómo llegar

LinkedIn **no se puede operar por accesibilidad en Dia** (su renderer no la activa, y
`--force-renderer-accessibility` tampoco la arregla). La vía que funciona es CDP:

```bash
# una sola vez, requiere cerrar el navegador (restaura pestañas)
open -a Dia --args --remote-debugging-port=9222
curl -s http://localhost:9222/json/version          # Chrome/156, protocol 1.3
curl -s -X PUT "http://localhost:9222/json/new?https://www.linkedin.com/feed/"
```

Después, todo son llamadas JS con `node cdp_eval.js --match linkedin.com --js "…"`.
En Chrome expone árbol de accesibilidad y se puede hacer con agent-desktop, pero **el operador
prefiere no usar Chrome**: se usa Dia.

## Navegar

- Feed: `https://www.linkedin.com/feed/`. El título con `(1)` delante = notificaciones sin leer.
- El DOM cambia de clases en cada despliegue (`b6b…`): **seleccionar por texto o `aria-label`**, nunca
  por clase.
- Botones útiles del feed: `Crear publicación`, `Nuevas publicaciones`, `Ocultar la publicación de X`.

## Crear el post y dejarlo en borrador (verificado)

1. Pulsar `Crear publicación` (botón con ese texto). Navega a `/sharing/compose` (no es un modal
   cerrado: hay 10 `div[role=dialog]` en el DOM y el composer está entre ellos).
   Ojo: el botón puede ser un `div[role=button]` con el texto entre espacios; buscar por
   `.includes('Crear publicación')`, no por igualdad.
2. Escribir en el editor (ProseMirror): `document.querySelector('[contenteditable=true]')` →
   `focus()` + `Input.insertText` (o `document.execCommand('insertText', …)`). `innerText` lo confirma.
3. El composer de **perfil personal** ofrece `Descartar` y `Publicar`, más un enlace con
   `aria-label="Programadas"` que **sí** abre la programación (ver más abajo).
4. Pulsar `button[aria-label="Descartar"]` → diálogo **«Guardar esta publicación como borrador?»**
   con `Descartar` y `Guardar como borrador`.
5. Pulsar el botón cuyo `innerText` sea exactamente `Guardar como borrador` → vuelve al feed y el
   texto de la página contiene «guardado el borrador.».
6. **Verificación independiente**: abrir otra pestaña en `/sharing/compose`; el editor vuelve a tener
   el texto, la mención y la página lo etiqueta `Borrador:`.

Nunca se pulsa `Publicar`.

### Formato dentro del post (verificado)

| Elemento | Cómo | Resultado |
|---|---|---|
| **Mención** | `insertText('@')`, esperar ~1,4 s, `insertText('nombre')`, esperar el typeahead, `ArrowDown` + `Enter` | se crea `<span data-type="mention" contenteditable="false"><strong>Nombre</strong></span>`; se conserva en el borrador |
| **Hashtag** | texto normal con `#IA #la agencia` | LinkedIn los detecta al publicar; sin widget |
| **Emoji** | `insertText` con el carácter (🚀🙌) o el botón `Mostrar selector de emojis` | entran como texto |
| **Negrita** | no existe en LinkedIn: se usan caracteres Unicode matemáticos (`𝐧𝐞𝐠𝐫𝐢𝐭𝐚`). Accesibilidad y copiar/pegar empeoran; avisar de ello | el editor los acepta como texto |
| **Enlace** | pegar la URL en el cuerpo (`https://la agencia.com`) y esperar: LinkedIn genera la vista previa; también existe «Añadir enlace» en el composer | enlace clicable al publicar |
| **Imagen** | ver abajo (`cdp_drop.js`) | se sube y se ve en el composer, **pero el borrador no la conserva** |

### Imagen: el file picker no se puede, el drop sí

- `button «Foto»` **no** abre un `input[type=file]` utilizable: el picker exige activación de
  usuario y `Page.setInterceptFileChooserDialog` no llega a recibir `fileChooserOpened`
  (probado con click JS y con click de ratón real vía `Input.dispatchMouseEvent`).
- Lo que funciona: `Input.dispatchDragEvent` (`dragEnter` → `dragOver` → `drop`) sobre la zona que
  el composer muestra con el texto **«Selecciona archivos para empezar»**, con
  `data.files = [ruta absoluta]` y `data.items[0].data` en base64. Verificado: la previsualización
  aparece con las dimensiones reales del PNG (800×420) y el composer ofrece `Texto alternativo`,
  `Editar` y `Eliminar`.
- **Al guardar como borrador la imagen se pierde** (comprobado reabriendo: `imgs blob = 0`). El
  borrador guarda solo el texto y las menciones. Si el post lleva imagen, hay que dejarlo abierto o
  publicarlo; no hay borrador con medios.

## Programar (sí existe; hasta 90 días)

En el composer hay un enlace con `aria-label="Programadas"` (no tiene texto propio: buscar por
`aria-label`, no por `innerText`). Al pulsarlo aparece **«Programar publicación / Programadas (n)»**
con campos `Fecha*` y `Hora*` (dos `input[type=text]`, `#_r_am_` y `#_r_ar_`) y el resumen
«Publicando el …». Botones: `Confirmar`, `Volver`, `Descartar`; y un enlace `Borrar`.

- **Límite duro: los próximos 90 días.** Una fecha fuera de rango vacía el campo y deshabilita
  `Confirmar` con el aviso «Selecciona una fecha dentro de los próximos 90 días». Comprobarlo
  siempre en el resumen antes de confirmar.
- Fijar la fecha con el setter nativo + eventos (funciona con React):
  `set.call(input,'30/12/2026'); input.dispatchEvent(new Event('input',{bubbles:true}));
  input.dispatchEvent(new Event('change',{bubbles:true})); input.blur()`
- `Confirmar` deja el post en estado programado (el composer muestra «Publicando el …» + `Editar`).
- Para deshacerlo: abrir `Programadas` y pulsar el enlace **`Borrar`** (es un `<a>`, no un
  `<button>`); el composer vuelve a su estado normal con el texto intacto.
- La fecha por defecto al abrir el diálogo es **hoy a la hora actual**: si se confirma sin cambiarla,
  el post se publica en ese momento. No confirmar nunca sin leer antes el resumen «Publicando el …».

## Trampas

- `Descartar` **no borra de inmediato**: abre el diálogo de guardar. Aun así, elegir el botón por su
  texto exacto; hay tres botones `Descartar` en la página (feed, diálogo, composer).
- Los botones del reproductor de vídeo del feed (`Close Modal Dialog`, `Play Video`) contaminan
  cualquier búsqueda por texto: filtrar por el contenedor o por `aria-label` específico.
- El texto del post debe marcarse como borrador de prueba si no es contenido real: es la cuenta del
  operador y el borrador se queda ahí.
- Cerrar la pestaña con CDP: `curl -s http://localhost:9222/json/close/<id>`.

## Alternativa sin CDP

`computer_use` con captura de pantalla y clics por coordenadas funciona (Dia se ve en la captura),
pero no permite leer el DOM ni verificar el borrador: es el último recurso, no el primero.
