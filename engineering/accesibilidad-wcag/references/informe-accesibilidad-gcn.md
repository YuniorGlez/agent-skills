# Informe de accesibilidad — Green Corridors Navigator

**Fecha:** 17 de octubre de 2026
**Ámbito revisado:** `plataforma/` (portada pública, inicio de sesión y las nueve pantallas de la aplicación) y el vídeo explicativo.
**Referencia:** el documento de la compañera (WCAG 2.2 AA, diseño universal) y los cuatro principios: perceptible, operable, comprensible, robusto.

> Cómo leer este informe: cada punto del documento va con **qué se cambió**, **en qué fichero** y **por qué**.
> Al final están los comandos para volver a comprobar todo y lo que queda fuera de esta revisión.

---

## 1. Resumen en cinco líneas

| Antes | Después |
|---|---|
| El mapa era la única vía para leer sus datos | Tabla «Alternativa textual al mapa»: **46 puertos y 65 tramos**, enlazados a sus fichas |
| axe-core daba violaciones en todas las pantallas (contraste, regiones desplazables, enlaces) | **0 violaciones** en las 12 rutas auditadas |
| Sin enlace de salto ni foco uniforme; con el texto al 200 % la barra lateral se salía | Enlace «Saltar al contenido», foco visible en todo, y **0 desbordes** a 320/360/390/768 px y con texto al 200 % |
| El vídeo no tenía subtítulos ni transcripción | **Subtítulos en ES/EN/FR** (VTT) + transcripción completa en texto |
| Siglas sin explicar (AIS, OPS, API, MCP, kVA, Metocean) | **Glosario** de 12 términos + pie de siglas en la portada + `abbr` en las tablas |

Verificación total: contraseña medida en **1.864 elementos de texto** (0 fallos), auditoría automática con **axe-core 4.12.1** (0 violaciones), pruebas de teclado/zoom/móvil en verde y los **11 tests e2e del propio proyecto** en verde.

---

## 2. Punto por punto, según el documento de referencia

### 2.1 Principios (perceptible · operable · comprensible · robusto)

No son un apartado aparte: cada cambio de abajo cae en uno de los cuatro. Lo que sí se hizo como decisión de fondo es **no depender nunca de una sola vía de acceso al dato** (ni solo el mapa, ni solo el color, ni solo la voz, ni solo el ratón).

### 2.2 A. Mapa de corredores marítimos

| Lo que pedía el documento | Qué se hizo | Por qué |
|---|---|---|
| Alternativa textual accesible al mapa | Nuevo componente `MapaAlternativa.tsx`, dentro del mapa: tabla de **puertos** (ámbito, estado OPS, instalaciones, en servicio, potencia, ficha) y tabla de **tramos** (puerto anterior → siguiente, escalas) | Un lienzo de MapLibre no es legible por un lector de pantalla: el mismo dato tiene que existir en texto. Va **dentro** de la página del mapa, no en otra sección, para que no se pierda el contexto |
| Consultar un puerto sin hacer clic en el marcador | Cada fila enlaza a `/puertos/<id>` y lleva un botón «Situar en el mapa» que selecciona el puerto, lo centra y actualiza el panel | El enlace funciona sin JavaScript y con teclado; el botón añade la parte visual sin sustituirla |
| Controles, capas y ventanas usables con teclado | El lienzo es enfocable y mantiene los controles propios de MapLibre (zoom, atribución) con sus etiquetas traducidas; se añadió una línea visible con las teclas (flechas, `+`, `−`) y se pasa a la tabla con el enlace de salto | MapLibre ya ofrece desplazamiento y zoom por teclado: lo que faltaba era **decirlo** y no dejar los marcadores como única puerta |
| No usar solo el color para rutas/estados | Los tres estados OPS se distinguen por **tamaño y color** (13 / 10 / 7 px en la leyenda) y el estado está en texto en la leyenda, en el panel y en la tabla | WCAG 1.4.1: el color no puede ser el único medio. Aquí se cumple por partida doble: forma en el mapa + texto en la tabla |
| Nombres y descripciones accesibles | Se reutiliza la etiqueta que MapLibre pone al lienzo (`Map.Title`) pero con el nombre completo «Mapa de puertos y rutas», y se le añade `aria-describedby` con las instrucciones | Antes el lienzo se anunciaba como «Mapa» a secas |
| Que funcione en pantallas pequeñas y con texto ampliado | Tablas dentro de contenedores desplazables **enfocables**; verificado a 320 px y con el texto al 200 % | Un desplazamiento horizontal que no se puede recorrer con teclado esconde datos |

### 2.3 B. Capas de información

| Lo que pedía | Qué se hizo | Por qué |
|---|---|---|
| Nombres claros en los botones | Los textos de los controles de MapLibre ya llegan traducidos desde el diccionario; se revisaron uno a uno | Un botón sin nombre es un botón que un lector anuncia como «botón» |
| Saber qué capas están activadas | Cada casilla va en una fila de **44 px** (objetivo táctil cómodo) y su estado lo comunica la propia casilla | Menos errores de pulsación; el estado no depende de un icono |
| Que los cambios se comuniquen | Cada activación/desactivación escribe un aviso en una región `role="status"`: «Capa «Estado OPS en puertos»: desactivada» | Antes, apagar una capa no producía ninguna señal para quien no ve el mapa |
| Que todo funcione con teclado y lector | Casillas y botones son elementos nativos, sin `div` con `onClick` | Se heredan teclado, foco y anuncio del navegador |

### 2.4 C. Tablas y gráficos

| Lo que pedía | Qué se hizo | Por qué |
|---|---|---|
| Encabezados bien identificados | `<caption>` y `scope="col"`/`scope="row"` en **todas** las tablas (puertos, fichas de puerto, fuentes, API, usuarios, claves, auditoría y la tabla alternativa del mapa) | Un lector de pantalla necesita saber qué columna encabeza cada celda |
| Leer los gráficos también en texto | El gráfico de barras de las fichas de fuente pasa a ser una **tabla** (concepto / valor): la barra queda como apoyo visual `aria-hidden` y el número va en texto | Antes era una lista con barras invisibles para el lector |
| Títulos, unidades y leyendas comprensibles | Cada gráfico lleva `<caption>` con título y unidad; las líneas de origen/destino llevan su leyenda | Se evita el «gráfico sin nombre» |
| Legibilidad en móvil, sin cortes | Tablas en contenedores con desplazamiento propio y `min-width: 0` para que no estiren la columna | Comprobado a 320 px |
| No transmitir diferencias solo por color | Los chips de estado llevan texto («En servicio», «Prevista», «Descartada») y el frescura del dato va en **texto y en color**: además se añadió la antigüedad también en texto oculto al lector visual («dato hasta 9 oct · Antigüedad del dato: hace 8 días») | Un dato viejo no puede parecer «ahora» solo por el tono del chip |

### 2.5 D. Asistente de voz y texto

| Lo que pedía | Qué se hizo | Por qué |
|---|---|---|
| Alternativa escrita siempre | La respuesta de voz ya se transcribía: ahora la transcripción tiene **título propio** (`Transcripción de la conversación`), el panel enlaza al asistente de texto («La voz no es obligatoria: puedes escribir la misma pregunta → Ir al asistente de texto») y el chat pasa a tener encabezado y `role="log"` | La voz deja de ser la única puerta |
| Botones con etiquetas claras | «Hablar»/«Terminar» pasan a **«Iniciar micrófono»/«Detener micrófono»** | Es lo que dice el documento, y describe la acción, no el medio |
| Poder detener fácil | Botón de detener siempre visible en la misma posición + **Escape** detiene la grabación, con la tecla indicada en la interfaz | Dos vías y sin buscar el botón |
| Informar de escuchando / procesando / respondiendo | El estado era `parado → conectando → escuchando`; ahora incluye **`procesando…`** (mientras se consultan datos) y **`respondiendo…`** (mientras habla el asistente), en una región `role="status"` | Sin esto, una pausa de dos segundos parece que se ha roto |
| Errores y permisos del micrófono comprensibles | Se mantienen los mensajes específicos (permiso denegado, sin micrófono, sesión cerrada, límite de voz, voz no configurada) y el de error va en `role="alert"` | Un error anunciado sin mover el foco |
| No obligar a usar la voz | Idem anterior: enlace al chat y transcripción permanente | |
| Mensajes interpretables con lector | Cada línea de la transcripción lleva «Tú:» / «Asistente:» en texto y la lista es `aria-live` | |

### 2.6 E. Formularios

Afecta a: inicio de sesión, editor de fuentes, editor de agentes, alta de usuarios y creación de claves API.

| Lo que pedía | Qué se hizo | Por qué |
|---|---|---|
| Etiquetas visibles y asociadas | Alta de usuarios y claves **no tenían etiqueta visible** (solo `placeholder`): ahora llevan etiqueta con `htmlFor`/`id`. Se mantienen las de login, fuente y agente | Un `placeholder` desaparece al escribir y no es una etiqueta |
| Campos obligatorios identificados | Nota común «Los campos marcados con * son obligatorios», asterisco visible con `aria-hidden` y `required` en el campo | El asterisco no ensucia el nombre accesible del campo; el `required` es lo que anuncia el lector |
| Explicar cómo corregir y señalar el campo | Mensajes por tipo de error (ya existían) + `aria-invalid` y `aria-describedby` que unen el campo con su mensaje | |
| Errores accesibles | Los mensajes de guardado usan `role="status"` y los de error `role="alert"` (antes todo iba como `status`, que no interrumpe) | Un error tiene que interrumpir; un «guardado» no |
| No perder lo escrito | Los formularios son controlados y no se limpian al fallar; se añadió la ayuda «mínimo 10 caracteres, se guarda cifrada» en la contraseña | |
| Todo completable con teclado | Todo son elementos nativos | |

### 2.7 F. Diseño visual y navegación

| Lo que pedía | Qué se hizo | Por qué |
|---|---|---|
| Contraste 4,5:1 / 3:1 | Nuevos tokens `--slate-ink` (#4a5a75) y `--warn-ink` (#8a3f06): el gris de marca #627792 daba **4,24:1** sobre el fondo y **3,91:1** en los chips; el aviso #b4540a sobre fondo crema daba 4,37:1 | Se corrige sin salir de la paleta del cliente: mismo tono, oscurecido lo justo |
| Tipografía legible | Se mantienen Poppins + Lato; ahora los títulos de caja del flujo de fuentes van en color sólido en vez de blanco al 70 % (daba 3,85:1) | |
| Comprensible al 200 % y en pantallas estrechas | Arreglado un fallo real: con el texto al 200 % la barra lateral y el menú se repartían en **varias columnas** y se salían de la pantalla (por `flex-wrap` + columna de 240 px). Ahora el menú es una sola columna con desplazamiento vertical. Además la barra de la portada pasa a dos líneas a 320 px, donde «Entrar» se salía | Es el fallo más serio que encontró la revisión, y no lo ve una herramienta automática |
| Botones y controles con tamaño suficiente | Área mínima de 40 px en botones y campos, filas de casilla de 44 px, botones de la barra lateral de la portada a 44 px | |
| Foco visible y no oculto | Regla global `:focus-visible` para **todo** lo enfocable (antes solo enlaces, campos y botones) + `scroll-padding-top` para que los saltos de sección no dejen el título debajo de la barra pegajosa | |
| Orden lógico de títulos y menús | Un `h1` por pantalla; se corrigieron las tablas de auditoría de usuarios (sin encabezados) y los grupos del menú llevan su rótulo | |
| Iconos con nombre accesible | Los iconos son decorativos (`aria-hidden`) y el texto que los acompaña es el que informa; el de «no» en la portada usaba `aria-label` en un `<span>` (no permitido): pasa a texto real para lector | |
| Mensajes de error, confirmación y carga comprensibles | «Cargando mapa…» pasa a `role="status"`; los avisos de resultado ya no son solo visuales; el mensaje de error de página mantiene su `role="alert"` | |

### 2.8 G. Lenguaje claro

| Lo que pedía | Qué se hizo | Por qué |
|---|---|---|
| Explicar las siglas la primera vez | **Nuevo glosario** (`/glosario`, 12 términos: AIS, OPS, kVA, API, MCP, Metocean, escala, puerto anterior → siguiente, granel sólido, LOCODE, EMC, dato hasta) enlazado desde el mapa, los puertos y el menú; las cabeceras usan `abbr` con su significado; y en el pie de la portada hay un resumen de siglas en una línea | Se mantiene el rigor y no se da por sabido lo que no lo es |
| Ayudas contextuales | El glosario dice **dónde** aparece cada término y añade el matiz honesto (p. ej. «la EMC se quedó en abril de 2018 y así se indica»; «AIS: no hay posiciones integradas todavía») | Explicar una sigla es también explicar su límite |

### 2.9 Vídeo (no estaba en el documento, pero lo pedía WCAG 1.2.2)

Al pasar la auditoría automática, el `<video>` de la portada salió marcado como **crítico**: un vídeo con voz y sin subtítulos no es accesible.

- **Subtítulos** `.vtt` para los tres vídeos (español, inglés y francés), 11/11/12 subtítulos.
- **Transcripción completa** en texto, desplegable bajo el vídeo.
- El texto de los subtítulos es **literal del guion** (`video/work/vo2/lines.txt`, `vo_en/`, `vo_fr/`) y los tiempos salen de **transcribir el audio real** de cada MP4 con `whisper small` en local. Se hizo así porque el vídeo que sirve la web es la versión de 57 s (y 64,9 y 61,2 s los otros dos): los tiempos del guion de la versión de 45 s no coincidían.
- El `<track>` se añade solo si el `.vtt` existe (`existsSync`), así que un idioma nuevo sin subtítulos no rompe nada.

---

## 3. Declaración de accesibilidad (nueva)

`/accesibilidad` — página **pública** (no pide cuenta):

- **Estado**: revisado contra WCAG 2.2 AA, con lo comprobable de forma automática y lo que depende de interacción.
- **Qué se ha hecho**: el mismo listado de este informe, en lenguaje llano.
- **Limitaciones conocidas**: el mapa (los marcadores no son enfocables uno a uno; la tabla es la vía prevista), la voz (necesita micrófono y funciona en local), la cartografía base de OpenStreetMap (no se puede adaptar), las fuentes de terceros sin licencia declarada y el **alcance** de la declaración (provisional; la oficial corresponderá a la Autoridad Portuaria, RD 1112/2018).
- **Cómo se ha comprobado**: los tres comandos del apartado 4.
- **Cómo comunicar un problema**: sin inventar un correo que no existe; se remite al equipo del producto.

El documento de la compañera avisa de que **«citar una ley no significa cumplir sus requisitos»**: por eso la página no afirma conformidad legal, solo lo medido, y deja explícito que la declaración oficial es de la Autoridad.

---

## 4. Verificación reproducible

Todo lo que sigue se ejecuta desde `plataforma/` con la aplicación en marcha (`bun run dev -- --port 3100`).

```bash
# 1. Auditoría automática (axe-core vía agent-browser): 0 violaciones
agent-browser a11y http://localhost:3100/mapa --tags wcag2a,wcag2aa

# 2. Contraste medido de TODO el texto visible (no estimado)
NODE_PATH=$(npm root -g) node scripts/contrast-check.mjs http://localhost:3100 <clave-superadmin>

# 3. Teclado, móvil, texto al 200 %, tabla alternativa y movimiento reducido
NODE_PATH=$(npm root -g) node scripts/a11y-check.mjs http://localhost:3100 <clave-superadmin>

# 4. No se ha roto nada de lo que ya funcionaba
bunx tsc@7 --noEmit --checkers 4
bun run i18n:check
E2E_USER_SUPERADMIN_PASSWORD=… E2E_USER_ANALISTA_PASSWORD=… E2E_USER_LECTOR_PASSWORD=… bunx e2e run
```

Resultados de esta revisión:

| Comprobación | Resultado |
|---|---|
| axe-core 4.12.1 en 12 rutas (`/`, `/accesibilidad`, `/login`, `/mapa`, `/puertos`, `/fuentes`, `/asistente`, `/agentes`, `/api-docs`, `/claves`, `/usuarios`, `/glosario`) | **0 violaciones** (antes: violación grave de contraste en todas las pantallas de la app, enlaces sin subrayar y 3 regiones desplazables sin teclado) |
| Contraste medido | **1.864 elementos de texto**, 0 fallos (se encontró y corrigió 1: el título de las cajas del flujo de fuentes, 3,85:1) |
| Móvil 320 / 360 / 390 / 768 px y texto al 200 % | **0 desbordes**, sin fugas de contenido (se corrigieron 2 fallos reales) |
| Teclado | Primer tabulador = «Saltar al contenido» y deja el foco en `#contenido` |
| Tabla alternativa del mapa | 111 filas operables con teclado; «Situar en el mapa» actualiza el panel y enlaza a la ficha |
| Movimiento reducido | Respetado (`prefers-reduced-motion` global y `jumpTo` en vez de `flyTo`) |
| `tsc@7 --noEmit --checkers 4` | 0 errores |
| `bun run i18n:check` | 8 idiomas completos (378 claves `app`, 289 `landing`; 1.015 claves traducidas en esta tanda) |
| `bunx e2e run` | **11/11 en verde** |

Dos detalles de método que conviene no olvidar:

1. **axe deja en «incomplete» lo que no puede medir**: en la portada marca 10 nodos del *hero* porque el texto se superpone al dibujo de isobatas. Medidos contra su fondo real dan entre 5,6:1 y 14,7:1, así que pasan. Por eso existe `contrast-check.mjs`: **la herramienta automática no es la prueba**.
2. **Una mejora de accesibilidad puede romper los tests del proyecto**: al añadir «(obligatorio)» dentro de la etiqueta, el nombre accesible del campo pasó de «Email» a «Email (obligatorio)» y los e2e que buscan `getByLabel("Email")` fallaron. Se resolvió con el patrón asterisco + `aria-hidden`, que además es el estándar. Los tests lo detectaron: ese es su valor.

---

## 5. Ficheros tocados

**Nuevos**

| Fichero | Para qué |
|---|---|
| `src/components/MapaAlternativa.tsx` | Alternativa textual al mapa (puertos y tramos) |
| `src/app/glosario/page.tsx` | Glosario de siglas y términos |
| `src/app/accesibilidad/page.tsx` | Declaración de accesibilidad (pública) |
| `src/components/landing/guiones.ts` | Locución literal de los tres vídeos |
| `public/media/explicativo.vtt`, `-en.vtt`, `-fr.vtt` | Subtítulos |
| `scripts/a11y-check.mjs` | Teclado, móvil, zoom 200 %, tabla alternativa, movimiento reducido |
| `scripts/contrast-check.mjs` | Contraste medido de todo el texto visible |

**Modificados** (19 componentes/páginas + estilos + proxy + 7 idiomas)

`globals.css` · `Shell.tsx` · `MapView.tsx` · `MapaAlternativa` · `Chat.tsx` · `Voice.tsx` · `FuenteViz.tsx` · `SourceEditor.tsx` · `AgentEditor.tsx` · `UsersManager.tsx` · `KeysManager.tsx` · `LangSwitch.tsx` · `app/{mapa,puertos,puertos/[id],fuentes/[id],usuarios,api-docs,login,page}.tsx` · `landing/{VideoExplicativo.tsx,FuentesVivas.tsx,landing.css}` · `proxy.ts` · `src/i18n/messages/*`.

---

## 6. Lo que no se ha hecho (y por qué)

| Cosa | Motivo |
|---|---|
| Operar los marcadores del mapa uno a uno con teclado | MapLibre no expone foco por marcador. La vía soportada es la tabla alternativa, que ya cubre el 100 % de los datos; forzarla exigiría reescribir la capa de marcadores |
| Sustituir la cartografía base por una con topónimos accesibles/adaptables | Es una decisión de producto (coste y licencias), no de accesibilidad de la interfaz |
| Traducir los subtítulos a los 5 idiomas restantes | El vídeo localizado solo existe en ES/EN/FR. El código ya añade el `<track>` en cuanto el `.vtt` esté |
| Modo de alto contraste / tema oscuro | No está pedido y el cliente fijó la interfaz clara |
| Declaración oficial de accesibilidad (RD 1112/2018) | Corresponde a la Autoridad Portuaria: la página actual es la provisional del prototipo y lo dice |
| Envío del enlace de la declaración a nadie | No se envía nada a terceros sin autorización |

---

## 7. Pendiente de decisión

1. **¿Se despliega ya?** Los cambios están en local y sin `commit` (`plataforma/` tiene 52 ficheros modificados y 10 nuevos sin seguimiento). No se ha hecho `commit`, `push` ni despliegue.
2. **¿Se pasa la declaración por el cliente?** Conviene que la Autoridad Portuaria vea el texto de `/accesibilidad` antes de publicarlo, sobre todo el apartado de limitaciones.
3. **Subtítulos de los vídeos**: ¿se generan también para los cinco idiomas que ven el vídeo en español, o se deja solo la transcripción?
4. **Revisión con lector de pantalla real** (VoiceOver/NVDA) de las pantallas de mapa y asistente: es lo único del documento de la compañera que no se puede automatizar del todo y que no se ha hecho en esta pasada.
