---
name: editar-xlsx-sin-perder-formulas
description: Editar un xlsx existente sin perder fórmulas ni estilos.
---

# Editar un .xlsx existente sin perder fórmulas, estilos ni imágenes

**Cuándo**: hay que añadir o editar hojas en un `.xlsx` que el usuario ya usa (su Excel de
facturas, su libro de cuentas). Si el fichero está en Drive, ver la sección de subida.

## La regla

**No uses openpyxl para reescribir un xlsx que el usuario ya usa.** Medido sobre
`Ventas2026.xlsx` (40 hojas de facturas, 252 KB): un `load_workbook` + `save()`
**borra los valores cacheados de todas las fórmulas** (el RESUMEN se queda con la columna
de totales vacía) y se lleva por delante los 40 `xl/drawings/drawingN.xml`. Pierdes datos
silenciosamente.

La vía correcta es **clonar la plantilla a nivel de XML y coser el ZIP**: así las hojas
existentes quedan **byte a byte idénticas** (verificado con sha256 parte por parte).

**Esto vale para REESCRIBIR un fichero que el usuario ya usa.** Para **crear un libro nuevo desde cero**
(informes, mapeos, exports) openpyxl es la vía correcta y cómoda: multi-hoja, anchos de columna, autofiltro,
paneles congelados, hipervínculos, hoja de metodología. Nada de eso pierde nada porque no hay original que
preservar. `openpyxl` no está en el python por defecto de este Mac (sí en `uv`):
`uv run --with openpyxl python3 build_xlsx.py`. Ejemplo de libro con hoja de metodología + una hoja por corte +
resumen isla × tipo: skill `ecosystem-entity-mapping` (`scripts/build_xlsx.py`).

## Anatomía de un xlsx (lo que hay que tocar para AÑADIR una hoja)

Un xlsx es un ZIP. Para añadir una hoja hay que editar **3 ficheros y añadir 1**:

| Fichero | Qué se le hace |
|---|---|
| `xl/workbook.xml` | insertar `<sheet state="visible" name="…" sheetId="N" r:id="rIdM"/>` justo antes de `</sheets>` |
| `xl/_rels/workbook.xml.rels` | `<Relationship Id="rIdM" Type="…/worksheet" Target="worksheets/sheetK.xml"/>` antes de `</Relationships>` |
| `[Content_Types].xml` | `<Override PartName="/xl/worksheets/sheetK.xml" ContentType="…spreadsheetml.worksheet+xml"/>` antes de `</Types>` |
| `xl/worksheets/sheetK.xml` | la hoja nueva (copia de la plantilla con las celdas cambiadas) |

Ojo: `sheetId` (atributo de la hoja, único) y `rId` (relación) son **espacios de nombres
independientes**; en los rels el `Target` **no** lleva barra inicial (`worksheets/sheetK.xml`).
Pero openpyxl sí la escribe en sentido contrario (`/xl/worksheets/…`), así que un lector
propio debe hacer `.lstrip("/")` o se rompe buscando `xl/xl/worksheets/`.

## Leer sin openpyxl

Ver `scripts/xlsx_read.py`: saca hojas, shared strings y celdas. Sirve para leer **y para
verificar** (es independiente del escritor, así que no valida sus propios errores).

## Escribir una celda conservando su estilo

Reemplaza solo el interior de la celda y conserva los atributos (`s="…"` = índice de estilo).
Para texto, usa `t="inlineStr"`: así **no hay que tocar `sharedStrings.xml`**, la parte más
frágil del formato.

```python
def setnum(xml, ref, valor):          # celda numérica
    m = re.search(r'<c r="%s"([^>]*?)(?:/>|>.*?</c>)' % ref, xml, re.S)
    attrs = re.sub(r'\s+t="[^"]*"', '', m.group(1))       # quita t="s" heredado
    return xml[:m.start()] + '<c r="%s"%s><v>%s</v></c>' % (ref, attrs, valor) + xml[m.end():]

def setstr(xml, ref, texto):          # celda de texto, sin tocar sharedStrings
    m = re.search(r'<c r="%s"([^>]*?)(?:/>|>.*?</c>)' % ref, xml, re.S)
    attrs = re.sub(r'\s+t="[^"]*"', '', m.group(1))
    esc = texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return xml[:m.start()] + '<c r="%s"%s t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>' % (ref, attrs, esc) + xml[m.end():]
```

**Riesgo de la regex de celda**: `<c r="D1"…` también casa dentro de `<c r="D11"…`. Es
determinista (gana el primero), pero si `D1` está vacía y autocerrada **se come su cierre y
descuadra el XML** → Excel repara el archivo. Comprueba con `zipfile.testzip()` y volviendo
a leer el fichero con un parser independiente.

## Fórmulas: escribe el valor TAMBIÉN

Si la plantilla tiene `<f>SUM(K27:K36)</f><v>252</v>` y al escribir dejas `<f>` sin `<v>`,
Excel recalcula al abrir; pero cualquier lector por datos (o el preview de Drive) puede ver
vacío. **Escribe la celda con `<v>`** (o con ambos). En una factura, un total sin valor
cacheado es un informe roto. Y ojo con las fórmulas compartidas (`t="shared" si="1"`): las
hojas hijas llevan `<f t="shared" si="1"/>` sin texto; lo más simple es escribirlas como
valor plano.

## El bug del ZIP que engorda el fichero 10x

```python
zf = zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED)
zf.writestr(zipfile.ZipInfo(name, ...), data)      # ❌ sale SIN COMPRIMIR (STORED)
```
Medido: 252 KB → 2.395 KB, con `compress_type: 0` en las 131 entradas. `writestr` con un
`ZipInfo` nuevo ignora el `compression` del constructor. Hay que ponerlo explícito:

```python
ni = zipfile.ZipInfo(name, date_time=zi.date_time)
ni.compress_type = zipfile.ZIP_DEFLATED
ni.external_attr = zi.external_attr                  # conserva permisos
zf.writestr(ni, data)                               # ✅ 265 KB
```

## Verificación obligatoria (antes de decir "hecho")

1. **Las partes originales no cambian**: sha256 de cada `xl/worksheets/*.xml` y de
   `xl/sharedStrings.xml` igual que en el original. Las únicas que deben diferir son
   `workbook.xml`, `workbook.xml.rels` y `[Content_Types].xml`.
2. `zipfile.testzip()` devuelve `None`.
3. El número de hojas es el esperado y **las originales conservan su orden**.
4. Las celdas nuevas tienen el valor correcto (leer con el parser independiente).
5. **Si se sube a Drive, verificar DESCARGANDO de Drive**, no del fichero local.

## Subir a Drive sobreescribiendo (xlsx, no Google Sheet)

Un `.xlsx` en Drive **no** se puede editar con la API de Sheets:
`400: This operation is not supported for this document. The document must not be an Office file.`
Se sube entero por el endpoint de upload:

```python
url = "https://www.googleapis.com/upload/drive/v3/files/%s?uploadType=media&fields=id,version" % SS
req = urllib.request.Request(url, data=open(f, "rb").read(), method="PATCH",
        headers={"Authorization": "Bearer " + TOK,
                 "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"})
```

Antes de subir: copia del original fuera de Drive y **compara `version`** para no pisar
cambios hechos entre medias. Después: avisa al usuario de que si tenía el fichero abierto,
debe cerrarlo y reabrir (su copia en memoria puede sobreescribir lo subido).

## Cuándo NO usar esto

- Si el usuario quiere una hoja nativa de Google Sheets → convierte el fichero o usa la API de Sheets.
- Si hay que reordenar/eliminar muchas hojas o tocar formato condicional complejo → el XML a
  mano empieza a ser peor que convertir a Google Sheet y trabajar por API.
- **Computer use no sirve para esto**: el driver puede no capturar la ventana del navegador
  (`capture` devuelve 0x0 y 0 elementos) y clonar una hoja a mano por UI no es verificable.
  Si el driver falla así, no insistas: usa esta vía por API y dilo.
