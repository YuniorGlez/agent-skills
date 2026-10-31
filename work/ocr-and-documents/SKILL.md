---
name: ocr-and-documents
description: "Extract text from PDFs/scans (pymupdf, marker-pdf)."
version: 2.3.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [PDF, Documents, Research, Arxiv, Text-Extraction, OCR]
    related_skills: [pdf, docx, powerpoint]
---

# PDF & Document Extraction

For DOCX: see the `docx` skill (create/edit) or use `python-docx` for structured reads.
For PPTX: see the `powerpoint` skill (full create/read/edit support).
For PDF manipulation (merge, split, forms, watermarks, creation): see the `pdf` skill.
This skill covers **text extraction from PDFs and scanned documents**.

## Step 1: Remote URL Available?

If the document has a URL, **always try `web_extract` first**:

```
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])
web_extract(urls=["https://example.com/report.pdf"])
```

This handles PDF-to-markdown conversion via Firecrawl with no local dependencies.

Only use local extraction when: the file is local, web_extract fails, or you need batch processing.

## Step 1b: Clasifica primero con pdf-inspector (router local)

**pdf-inspector** (Rust, MIT, Firecrawl, v0.2.6) clasifica un PDF en ~10-50ms —
sin OCR, sin ML, sin API — y si es text-based extrae Markdown con orden de
lectura multi-columna y tablas (gana a pymupdf4llm y markitdown en el bench
opendataloader: overall 0.875, tablas 0.814, 0.47s/200 docs). Instalado en
un venv con `pdf-inspector` instalado (wheel precompilado; Rust solo si hay que
compilar).

```bash
# Clasificar + extraer Markdown (lo normal)
python3 -c "
import pdf_inspector
r = pdf_inspector.process_pdf('document.pdf')
print(r.pdf_type, r.confidence, r.page_count)  # text_based | scanned | image_based | mixed
print(r.markdown)
"

# Solo clasificación rápida (para rutear sin extraer)
python3 -c "
import pdf_inspector
r = pdf_inspector.detect_pdf('document.pdf')
print(r.pdf_type, r.confidence, r.pages_needing_ocr)
"
```

**Decisión de ruteo**:
- `text_based` (conf alta) → usar su Markdown directamente. Terminado, sin más herramientas.
- `mixed` → extraer con pdf-inspector y revisar `pages_needing_ocr`; pasar SOLO esas páginas a marker-pdf si el contenido importa.
- `scanned` / `image_based` → marker-pdf (o avisar si no hay ~5GB libres).

API útil: `process_pdf_bytes(data)` (adjuntos de Gmail/APIs sin tocar disco),
`extract_pages_markdown(path, pages=[...])` (Markdown por página con
`needs_ocr` por página), `extract_text_in_regions(path, regions)` (recortes
por bounding box), `extract_text_with_positions` (items con X/Y y font).

## Step 1c: Office docs (docx/pptx/xlsx/xlsm/odt/rtf/epub/csv) → anydoc (default)

**anydoc** (`@firecrawl/anydoc`, Rust, v0.1.7, instalado vía `bun i -g @firecrawl/anydoc`) convierte documentos Office a GitHub-Flavored Markdown 100% local en **0.05-0.08s/doc** (verificado 8-ago con lote real de clientes: docx ULPGC con tablas, xlsx catálogo Acciona 53KB, xlsm encuestas, pptx).

```bash
anydoc documento.docx                  # Markdown a stdout
anydoc documento.xlsx -o salida.md     # a fichero
anydoc - --format csv < data.csv       # stdin
./scripts/anydoc_batch.sh DIR_IN DIR_OUT   # lote completo
```

Gana al pipeline python-docx/python-pptx/openpyxl: genera tablas Markdown reales (python-docx pierde las tablas de Word), maneja xlsm, y es un binario único sin deps. Para PDFs: **anydoc y pdf-inspector producen el MISMO markdown** (mismo motor Firecrawl; verificado con diff) — pero pdf-inspector sigue siendo el router porque añade la clasificación (`text_based`/`scanned`/`image_based`) y anydoc **falla con error limpio en PDFs escaneados** («OCR is required») → rutear esos a marker-pdf.

## Step 2: Choose Local Extractor

| Feature | pymupdf (~25MB) | marker-pdf (~3-5GB) |
|---------|-----------------|---------------------|
| **Text-based PDF** | ✅ | ✅ |
| **Scanned PDF (OCR)** | ❌ | ✅ (90+ languages) |
| **Tables** | ✅ (basic) | ✅ (high accuracy) |
| **Equations / LaTeX** | ❌ | ✅ |
| **Code blocks** | ❌ | ✅ |
| **Forms** | ❌ | ✅ |
| **Headers/footers removal** | ❌ | ✅ |
| **Reading order detection** | ❌ | ✅ |
| **Images extraction** | ✅ (embedded) | ✅ (with context) |
| **Images → text (OCR)** | ❌ | ✅ |
| **EPUB** | ✅ | ✅ |
| **Markdown output** | ✅ (via pymupdf4llm) | ✅ (native, higher quality) |
| **Install size** | ~25MB | ~3-5GB (PyTorch + models) |
| **Speed** | Instant | ~1-14s/page (CPU), ~0.2s/page (GPU) |

**Decision**: primero clasifica con pdf-inspector (Step 1b) — si es `text_based`, su Markdown ya es suficiente. pymupdf queda para operaciones simples (split/merge/search) y extracción rápida; marker-pdf SOLO para `scanned`/`image_based` (OCR), ecuaciones, formularios o análisis de layout complejo.

If the user needs marker capabilities but the system lacks ~5GB free disk:
> "This document needs OCR/advanced extraction (marker-pdf), which requires ~5GB for PyTorch and models. Your system has [X]GB free. Options: free up space, provide a URL so I can use web_extract, or I can try pymupdf which works for text-based PDFs but not scanned documents or equations."

---

## Step 3: ¿Merece la pena cambiar de parser?

Cuando llega un parser nuevo (un lanzamiento en X/HN, un «#1 en tres benchmarks»), no se
adopta por su README: se mide contra el corpus del usuario. Orden corto:

1. **¿Corre aquí?** Casi todo SOTA exige Linux + NVIDIA BF16; en Mac no hay self-host (solo
   API o GPU alquilada). Decídilo antes de medir calidad.
2. **Licencia real**: `gh api repos/... --jq .license.spdx_id` da `NOASSERTION` cuando hay
   cláusula añadida — baja y lee el LICENSE (OXR: Apache 2.0 con umbral comercial de 2M USD).
3. **API gratuita antes que GPU**: si el vendor expone endpoint libre, úsalo con su CLI
   oficial cambiando solo `--base-url`; números reales en minutos.
4. **Mide** 2-3 documentos del corpus (uno con tablas densas) contra `pdftotext -layout` con
   `scripts/cmp_text.py`; las palabras perdidas en cabecera/pie son filtrado por diseño, no
   fallo. Comprueba dominio: en español OXR tira el `¿` y convierte iconos decorativos en
   enlaces de imagen remotos (ruido para el LLM).
5. **Veredicto por defecto: complemento, no reemplazo** — fallback para documentos donde
   pdf-inspector/marker revientan, y el A/B final lo elige el usuario con sus PDFs.

Detalle, umbrales y lectura de benchmarks en `references/evaluar-parser-candidato.md`.
Candidatos ya medidos: OXR-1.0 (ahí; gratis por API, no corre en Mac) y LightOnOCR-3 en
Apple Silicon (`references/lightonocr3-local.md`).

---

## pymupdf (lightweight)

```bash
pip install pymupdf pymupdf4llm
```

**Via helper script**:
```bash
python scripts/extract_pymupdf.py document.pdf              # Plain text
python scripts/extract_pymupdf.py document.pdf --markdown    # Markdown
python scripts/extract_pymupdf.py document.pdf --tables      # Tables
python scripts/extract_pymupdf.py document.pdf --images out/ # Extract images
python scripts/extract_pymupdf.py document.pdf --metadata    # Title, author, pages
python scripts/extract_pymupdf.py document.pdf --pages 0-4   # Specific pages
```

**Inline**:
```bash
python3 -c "
import pymupdf
doc = pymupdf.open('document.pdf')
for page in doc:
    print(page.get_text())
"
```

---

## marker-pdf (high-quality OCR)

```bash
# Check disk space first
python scripts/extract_marker.py --check

pip install marker-pdf
```

**Via helper script**:
```bash
python scripts/extract_marker.py document.pdf                # Markdown
python scripts/extract_marker.py document.pdf --json         # JSON with metadata
python scripts/extract_marker.py document.pdf --output_dir out/  # Save images
python scripts/extract_marker.py scanned.pdf                 # Scanned PDF (OCR)
python scripts/extract_marker.py document.pdf --use_llm      # LLM-boosted accuracy
```

**CLI** (installed with marker-pdf):
```bash
marker_single document.pdf --output_dir ./output
marker /path/to/folder --workers 4    # Batch
```

---

## Arxiv Papers

```
# Abstract only (fast)
web_extract(urls=["https://arxiv.org/abs/2402.03300"])

# Full paper
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])

# Search
web_search(query="arxiv GRPO reinforcement learning 2026")
```

## Split, Merge & Search

pymupdf handles these natively — use `execute_code` or inline Python:

```python
# Split: extract pages 1-5 to a new PDF
import pymupdf
doc = pymupdf.open("report.pdf")
new = pymupdf.open()
for i in range(5):
    new.insert_pdf(doc, from_page=i, to_page=i)
new.save("pages_1-5.pdf")
```

```python
# Merge multiple PDFs
import pymupdf
result = pymupdf.open()
for path in ["a.pdf", "b.pdf", "c.pdf"]:
    result.insert_pdf(pymupdf.open(path))
result.save("merged.pdf")
```

```python
# Search for text across all pages
import pymupdf
doc = pymupdf.open("report.pdf")
for i, page in enumerate(doc):
    results = page.search_for("revenue")
    if results:
        print(f"Page {i+1}: {len(results)} match(es)")
        print(page.get_text("text"))
```

No extra dependencies needed — pymupdf covers split, merge, search, and text extraction in one package.

---

## Notes

- `web_extract` is always first choice for URLs
- Antes de adoptar un parser nuevo: `scripts/cmp_text.py` da recall/precisión contra
  `pdftotext -layout`; el leaderboard del vendor no es una medición (ver Step 3)
- pdf-inspector is the default local router: classify first (~10-50ms), use its Markdown for text-based PDFs, fall back to marker-pdf only for scanned/image_based pages
- pymupdf is the safe default — instant, no models, works everywhere
- marker-pdf is for OCR, scanned docs, equations, complex layouts — install only when needed
- Both helper scripts accept `--help` for full usage
- marker-pdf downloads ~2.5GB of models to `~/.cache/huggingface/` on first use
- **Pitfall (macOS)**: marker-pdf leaves a `surya.fast_layout.server` process resident (~1.8GB RSS, 0% CPU, launched via launchd, port is ephemeral). After OCR work, kill it: `pkill -f surya.fast_layout.server`. It cold-starts again on the next OCR, no data lost. Check with `ps aux | grep surya`.
- For Word docs: `pip install python-docx` (better than OCR — parses actual structure)
- For PowerPoint: see the `powerpoint` skill (uses python-pptx)
