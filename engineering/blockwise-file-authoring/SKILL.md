---
name: blockwise-file-authoring
description: Escribir ficheros largos por bloques y verificar resultado.
---

# Blockwise File Authoring

Escribir artefactos de texto/markdown largos en bloques y verificarlos con un script — nunca generar el fichero completo en una sola llamada.

## Cuándo usar
- Generar cualquier fichero de texto/markdown largo (>~15KB, >~100 intervenciones/líneas): transcripciones limpias, informes, documentación, migraciones de contenido.
- Cuando una sola generación del fichero completo arriesga: timeout del proxy/gateway (ej. HTTP 524 de Cloudflare con LLMs lentos, origin >120s), truncación silenciosa, o respuestas que mueren a mitad y dejan el fichero sin escribir.
- Cuando el fichero debe ser fiel a una fuente estructurada (raw → clean, borrador → final) y necesita verificación automática.

## Reglas (jul 2026, preferencia explícita del usuario — mandatorias)
1. **Nunca escribir el fichero completo de una vez.** Siempre `write_file` con el primer bloque + appends sucesivos.
2. Tamaño por bloque: ~100 intervenciones / ~10-15KB máx por llamada. Si un bloque va a ser más largo, partirlo.
3. Append con heredoc **citado** (sin interpolación):
   ```bash
   cat >> "ruta/fichero.md" << 'EOF'
   ...bloque de contenido...
   EOF
   ```
   - El delimitador SIEMPRE entre comillas (`'EOF'`): sin ellas, `$`, backticks y `\` se interpretan y corrompen el contenido.
   - Tras cada append, comprobar el tamaño acumulado: `wc -c ruta/fichero.md`.
   - El heredoc equivale a un patch pero sin re-leer el fichero — más rápido y sin riesgo de anchors no únicos.
4. **Nunca uses un segundo `write_file` sobre la misma ruta para «añadir una parte»: REEMPLAZA el fichero entero** (ver Pitfalls). El único mecanismo de append es el heredoc citado del punto 3. Tras el último bloque, **verificar en disco y estructuralmente** — nunca fiarse del estado reportado:
   - El fichero existe y tiene tamaño razonable (`ls -la`, `wc -c`).
   - Si el formato es `Nombre [MM:SS]: texto` (tl;dv y similares): `python3 scripts/verify_turns.py <raw> <clean>` (script del skill).
   - La última línea/timestamp del fichero coincide con la fuente.

## Pitfalls
- **Duplicar contenido al fusionar fragmentos**: al fusionar un fragmento de continuación en el turno padre (mismo hablante, timestamps adyacentes, ej. `[50:40]`+`[50:45]`), es fácil escribir por error el contenido de un turno posterior en el timestamp intermedio, duplicándolo. El verificador detecta texto duplicado entre turnos.
- **Fusiones intencionadas ≠ pérdida**: eliminar muletillas y fusionar continuaciones reduce el nº de turnos vs raw (normal). El verificador distingue: timestamps del raw ausentes = revisar si son merges intencionados; turnos de más que el raw = error real.
- **No fusionar turnos del mismo hablante si otro hablante interrumpió entre medias** (aunque el interjector sea eliminable, ej. "Vale.", "Sí."): el raw los marca como turnos con timestamps distintos y el clean debe conservarlos separados. Validado jul 2026: fusionar [25:50]+[26:03] de un mismo hablante separados por un "Vale." de otro obligó a deshacerlo con patches para restaurar la fidelidad.
- **Timestamps duplicados en el raw** (mismo [MM:SS] en varios turnos, hablantes solapados, ej. [09:47], [20:00], [30:52]) son legítimos: comparar SIEMPRE timestamps únicos (`sort -u`), nunca el recuento bruto de ocurrencias — nunca coincide con el clean aunque esté perfecto.
- **Heredoc sin comillas** corrompe contenido con `$`/backticks (ej. texto con `tl;dv`, `$PATH`, `console.log`).
- **Un solo bloque gigante** = riesgo de 524/truncación. Dividir ANTES, no cuando ya ha fallado.
- **Tras un 524, verificar en disco antes de relanzar**: el agente puede reportar "completed" aunque la última llamada muriera y el fichero no exista o esté incompleto.
- **BSD grep en macOS no soporta `\S`, `\d`, `\w` en `-E`** (POSIX ERE): `grep -cE '^\S+ '` devuelve 0 matches SIN error (silencio peligroso). Para conteos/validaciones usar ERE puro: `grep -oE '\[[0-9]{2}:[0-9]{2}\]'` o `[[:space:]]` en vez de `\s`.
- **Nunca recomponer un fichero con `split()` + `join()` sobre el literal de una etiqueta o cabecera que quieras conservar**: `s.split('<section class="page', 1)` + rejoin BORRA los tags reales y deja fragmentos huérfanos (`">`) que solo se detectan al grepear el fichero. Síntoma típico: el fichero "pesa" y el contenido parece estar, pero `grep -c '<section'` devuelve 0. Para renumerar o transformar repeticiones usa `re.sub` con contador sobre el texto COMPLETO (nunca split/rejoin), y **tras cada write verifica los conteos estructurales**: `s.count('<etiqueta') == s.count('</etiqueta>') == n_esperado`. Un write aparentemente exitoso (bytes escritos, `verified: true`) puede haber dejado el fichero sin sus etiquetas — la verificación estructural es la única prueba.
- **Partir un documento y escribir la «segunda parte» con `write_file` BORRA la primera**: `write_file` SIEMPRE reemplaza el fichero completo — no existe modo append. Si divides un documento largo en partes y haces `write_file` de la parte 2 sobre la misma ruta, el fichero queda SOLO con la parte 2 y la parte 1 desaparece sin ningún error (`verified: true`, bytes escritos, lint OK). Detección inmediata: `grep -n '^## ' fichero` tras CADA escritura — si un documento que iba por la sección 0 empieza ahora por la 6, has pisado el head. Recuperación sin rehacerlo todo: conservar el head recién escrito y la cola en `/tmp`, y recomponer con `cat /tmp/head.md /tmp/tail_backup.md > fichero.md`, volviendo a comprobar la lista de secciones. Corolario: al partir un documento, escribe la PRIMERA parte con `write_file` y TODAS las siguientes con heredoc citado.
- **`write_file` + appends sucesivos sobre un fichero que ya tiene un writer previo**: si el mismo fichero se reescribe varias veces en la misma sesión (p.ej. renumera → reescribe → renumera), lee SIEMPRE el estado real de disco antes de la nueva transformación y comprueba los conteos tras escribir; encadenar transformaciones sobre un estado supuesto multiplica el riesgo de corrupción silenciosa.
- **Heredoc y backticks en el comando**: si el bloque a escribir contiene backticks (código, comandos, markdown), un heredoc sin citar o un `python3 -c` embebido rompen el shell (`unexpected EOF while looking for matching`). Escribir el contenido con `write_file` a un `.py` y ejecutarlo con `python3 /tmp/<script>.py` evita la clase entera de problemas de quoting y las aprobaciones repetidas de pipe-a-intérprete.
- **`patch` borra líneas de contexto no reproducidas**: en `patch mode=replace`, cualquier línea del `old_string` ausente del `new_string` se ELIMINA del fichero. Si usas la línea siguiente como ancla de unicidad (ej. la línea `> **Para quién:**` tras una cabecera que quieres mantener) y no la repites en `new_string`, la borras y fusionas el texto con la línea anterior. Regla: `old_string` = SOLO el texto a sustituir (sin líneas que quieras conservar); tras cada patch, leer el diff devuelto buscando borrados inesperados antes de lanzar el siguiente patch (visto en edición de handoff 8-ago-2026: cabecera fusionada, restaurada con un patch de fix).

- **Markdown que tiene que RENDERIZAR: línea en blanco antes de toda lista.** Python-Markdown (y la mayoría de conversores) absorbe `- item` como texto del párrafo anterior si no hay blanco entre medias: los ítems se ven como prosa con guiones, las casillas `- [ ]` NO se renderizan (quedan como `[ ]` literal) y bloques enteros —gates, criterios de aceptación— salen colapsados en una sola línea. En documentos generados campo a campo (una línea por dato, sin blancos) pasa SIEMPRE, y no se nota hasta que alguien convierte el markdown. Normalizar antes de convertir: insertar línea en blanco cuando una línea es ítem (`-`/`*`/`1.`) y la anterior no lo es ni es tabla/cita/código/encabezado.
- **Bloques de metadatos como líneas consecutivas `**Clave:** valor` se unen en un párrafo ilegible.** Markdown los trata como un solo párrafo: si el documento va a renderizarse (HTML/PDF), escríbelos como tabla de dos columnas (`| | |` + filas `| **Clave** | valor |`) — y si van a portada, la tabla se extrae y se pinta ahí.
- **Los diagramas se verifican por su FUENTE y por el DOM, nunca con visión**: al pedirle a un modelo de visión que describa un diagrama renderizado inventa defectos que no existen (reportó ids de nodo duplicados y etiquetas de clúster cruzadas en un grafo que estaba limpio). Ground truth: (a) parsear el bloque del propio fuente — etiquetas de `subgraph`, ids declarados vs. los referenciados en los `-->`, ids duplicados; (b) contar en el DOM renderizado `.node`, `.edgePath` y `.cluster`, y errores de consola. La visión se usa solo para «¿se lee bien / hay cajas cortadas?», nunca para datos concretos que se puedan contar. Para renderizar y comprobar un diagrama basta un HTML con `<pre class="mermaid">`, el import del módulo ESM desde CDN y ~7s de espera antes de contar.

## Scripts
- `scripts/verify_turns.py` — Verifica un fichero "limpio" vs su raw en formato `Nombre [MM:SS]: texto`: turnos por hablante (raw vs clean), timestamps del raw ausentes en el clean, orden cronológico de los timestamps, coincidencia del último timestamp, y contenido duplicado entre turnos. Exit 0 = OK (con avisos de revisión manual), 1 = errores. Uso: `python3 scripts/verify_turns.py <raw> [<clean>]` (si solo se pasa el raw, deriva `clean/<base>_clean.md`).

## Relación con otros skills
- Para pares de documentos emparejados (PRD + roadmap, plan + tareas) existe un verificador listo: `scripts/verify_prd_roadmap.py` — paridad fichas de tarea ↔ tabla de dependencias, **DAG sin ciclos**, cobertura de todos los requisitos del PRD, integridad de los nodos mermaid y aviso si un documento empieza por la sección equivocada (head pisado, ver Pitfalls). Uso: `python3 scripts/verify_prd_roadmap.py [PRD.md] [ROADMAP.md]`; exit 1 si hay fallos.
  - **La cobertura se comprueba por ID, no «a ojo»**: cada requisito del PRD (`**F1.`, `**F2.`, …) tiene que aparecer por su ID en alguna ficha de tarea o fila de la tabla. Leer 29 requisitos contra 39 fichas parece exhaustivo y aun así deja cinco sin cubrir en silencio — el grep de IDs es lo que lo detecta. Un requisito sin tarea es un hueco de alcance, no un olvido cosmético.
  - **Paridad en los dos sentidos**: ficha sin fila en la tabla de dependencias Y fila sin ficha son ambos errores. Y **IDs únicos**: una pasada de renumeración duplica con facilidad (`T2.10a` vs `T2.1`).
  - El verificador no decide si la cobertura es CORRECTA: puede que un requisito esté cubierto por una tarea con otro nombre, o que la referencia al ID se haya añadido al texto sin que la tarea exista de verdad (pasar el verificador no es haberlo resuelto — comprobar que la tarea hace lo que el requisito pide).
- El pipeline de transcripciones (skill `clean-transcriptions-auto`, del usuario) aplica estas reglas con tamaños concretos; si está adoptado por el curator, las reglas viven allí. Este skill es la técnica genérica reutilizable en cualquier generación de ficheros largos.
