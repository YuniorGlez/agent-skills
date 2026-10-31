# Spanish Entity Fiscal Data (CIF/NIF) Lookup

Research pattern for finding CIF/NIF (tax ID) of Spanish public entities, universities,
foundations, and companies from their official websites.

## Pattern Summary

Spanish public entities are legally required to publish their CIF/NIF in the Aviso Legal
(Legal Notice) of their website. Public sector entities (universities, foundations) also
publish it in their Portal de Transparencia (Transparency Portal), often in downloadable
PDFs.

## Entities Covered

| Type | CIF prefix | Example |
|------|-----------|---------|
| Public University | Q (plus province code) | Q3518001G (ULPGC) |
| Canarian Foundation | G | G76001007 (FPCT ULPGC) |
| Private company | Letter varies by type | — |

## Step-by-Step Workflow

### 1. Start with the Entity's Own Website (skip search engines)

Search engines (Google, Bing) aggressively block automated browsers with CAPTCHAs.
Always navigate directly to the entity's website first.

### 2. Check Aviso Legal (Legal Notice) — Fastest Path

The CIF is almost always in the first paragraph of the Aviso Legal page.

**Common URL patterns:**
- `https://<domain>/aviso-legal`
- `https://<domain>/es/aviso-legal`
- `https://<domain>/sobre-esta-web/aviso-legal` (ULPGC pattern)
- In the footer: look for "Aviso Legal" or "Legal Notice" link

Once on the page, look for patterns like:
- "con CIF Q-3518001-G" or "con CIF Q3518001G"
- "con NIF G-76001007"
- "Código de Identificación Fiscal (CIF)"

### 3. Check Portal de Transparencia (Transparency Portal)

If the Aviso Legal doesn't show it (some foundation sites), go to:

- `https://<domain>/transparencia`
- `https://<domain>/es/transparencia`

Look for section **"1. INFORMACIÓN INSTITUCIONAL"** — this usually contains a PDF
titled something like:
- `1.1_1001_Información_general_de_la_entidad...pdf`

### 4. Extract CIF from PDFs

**Tool: `pdftotext`** (available on macOS via Homebrew: `brew install poppler`)

```bash
pdftotext /path/to/document.pdf - | grep -i -B2 -A2 "cif\|nif\|identificación fiscal"
```

This will output lines like:
```
Código de Identificación Fiscal (CIF)

El Código de Identificación Fiscal (CIF) de la Fundación... es G-76001007
```

### 5. Fallback: Check Cookie Notice / Footer

Many Spanish sites show the full legal entity name in their cookie consent banners
or page footers. The CIF itself may not be there, but the full entity name helps
narrow the search.

### 6. Verify on Official Registry (if needed)

For verified CIF lookups in bulk, the Spanish government's official sources:
- CIRCE (Centro de Información y Red de Creación de Empresas)
- BORME (Boletín Oficial del Registro Mercantil)

## Known Entity Data (Confirmed from Official Sources)

### Universidad de Las Palmas de Gran Canaria (ULPGC)
- **CIF/NIF**: Q-3518001-G
- **Razón Social**: Universidad de Las Palmas de Gran Canaria
- **Dirección**: C/ Juan de Quesada, 30, 35001 Las Palmas de Gran Canaria, España
- **Source**: https://www.ulpgc.es/sobre-esta-web/aviso-legal

### Fundación Canaria Parque Científico Tecnológico de la ULPGC (FPCT)
- **CIF/NIF**: G-76001007
- **Razón Social**: Fundación Canaria Parque Científico Tecnológico de la Universidad de Las Palmas de Gran Canaria (FCPCT de la ULPGC)
- **Dirección**: C/ Practicante Ignacio Rodríguez, s/n, Edificio Polivalente III, Campus Universitario de Tafira, 35017 Las Palmas de Gran Canaria, España
- **Nº Registro**: 269 (Registro de Fundaciones)
- **Source**: PDF de Transparencia (fpct.ulpgc.es) — Información General de la Entidad