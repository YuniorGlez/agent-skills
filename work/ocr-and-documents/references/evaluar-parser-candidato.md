# Evaluar un parser documental candidato (sin adoptarlo por el leaderboard)

Un parser nuevo se adopta por **medición sobre el corpus del usuario**, no por su propio
README. El orden de gates evita gastar tiempo en candidatos que no pueden entrar.

## Gate 0 — ¿corre en esta máquina?

Léelo antes de instalar nada: casi todos los SOTA de parsing (OXR, PaddleOCR-VL, MinerU)
exigen **Linux + NVIDIA BF16** (24 GB mínimo). En un Mac Apple Silicon no hay self-host;
las opciones son API del proveedor o GPU alquilada. Si no corre, decide API-sí-o-no ANTES
de medir calidad, y dilo en el veredicto.

## Gate 1 — licencia real, no el badge

`gh api repos/<org>/<repo> --jq .license.spdx_id` devuelve `NOASSERTION` cuando hay
cláusula añadida. Baja el LICENSE y léelo:

```bash
curl -s https://raw.githubusercontent.com/<org>/<repo>/main/LICENSE | head -20
```

OXR-1.0 es Apache 2.0 **con umbral**: uso comercial gratis solo por debajo de 2M USD de
facturación o financiación; por encima hay que comprar licencia. No es Apache limpio y es
una obligación que se hereda al entregar a cliente.

## Gate 2 — ¿es un repo de verdad o un lanzamiento?

```bash
gh api repos/<org>/<repo> --jq '{stars:.stargazers_count,created:.created_at,issues:.open_issues_count,pushed:.pushed_at}'
```

Señal buena: pipeline completo (`pipeline/`, `server/`, `services/`, tests unitarios por
módulo, Dockerfile), no un `inference.py` de demo. Un repo de semanas con lanzamiento en
prensa no es descarte por sí solo, pero exige medir más.

## Vía rápida: API gratuita del proveedor antes de montar GPU

OXR expone API sin registro que entiende la CLI oficial. Números reales en minutos:

```bash
cd <scratch> && mkdir -p out            # --out debe EXISTIR o la CLI aborta
uv venv -p 3.12 .venv && uv pip install --python .venv/bin/python somark
.venv/bin/somark --base-url https://free-oxr.somark.ai/api/v1 --api-key dummy \
  parse doc.pdf --formats md,json --out ./out
```

- Límites de esa API: **10 MB y 20 páginas** por petición. Pasarse devuelve un `400` sin
  cuerpo útil; trocea con `pdfseparate -f 1 -l 8` + `pdfunite` y reintenta.
- `SoMarkWarning: feature_config.* is accepted but ignored` es normal: OXR solo implementa
  `keep_header_footer`.
- Encolada: ~1,8 s/página. Vale para medir, no para producción (el propio vendor lo dice).

## Medición mínima (esto es el veredicto)

1. Elige **documentos del corpus real**, no demos del vendor: uno digital con tablas
   densas, uno de dominio del cliente y, si hay, uno escaneado.
2. Ground truth = `pdftotext -layout` sobre el PDF digital. Con `scripts/cmp_text.py` salen
   recall/precisión multiset y las palabras que faltan.
3. Interpreta las pérdidas antes de dar el número por malo: cabeceras y pies (banner del
   boletín, URL de sede, numeración) se filtran **por diseño** — si `missing` está dominado
   por esos tokens, el recall real del cuerpo es varios puntos mayor. Referencia medida en
   una orden del BOC (español jurídico, 8 páginas): 94,6 % recall / 99,4 % precisión brutos,
   casi todo lo perdido era cabecera del boletín.
4. Comprobaciones de dominio que ningún benchmark cubre: signos de apertura del español
   (`¿` `¡`) — OXR los tira, `¿POR QUÉ` sale como `?POR QUÉ`; y ruido para agentes —
   iconos decorativos convertidos en enlaces a imágenes alojadas en el dominio del proveedor
   (un CV devolvió 8 PNG): limpia esos `![](...)` antes de pasar el Markdown a un LLM.
5. Ritmo con reloj propio, no el `pages/s` del vendor (medido en una RTX PRO 6000).

## Cómo leer sus benchmarks

- Los scores de los rivales suelen estar **copiados de sus papers**; los del modelo nuevo,
  medidos por el propio equipo en su harness. Etiqueta [MKT] el ranking entero.
- Diferencia de 0,2-0,3 puntos en el overall = ruido, no liderazgo (OXR 87,84 vs 87,60 en
  olmOCR-bench). La ventaja reproducible está en **tablas** (+3 a +7 puntos sobre
  PaddleOCR-VL-1.6).
- Un «#1 en tres benchmarks» se traduce a: candidato para tablas, formularios y fórmulas;
  nunca a sustituto del pipeline entero.

## Veredicto por defecto

Complemento, no reemplazo: pdf-inspector → marker sigue siendo el camino; el candidato
entra como **fallback para documentos donde el local revienta** y solo tras un A/B con 3-4
PDFs que elige el usuario.

Candidatos ya medidos: OXR-1.0 (arriba) y LightOnOCR-3 en local (`lightonocr3-local.md`).
