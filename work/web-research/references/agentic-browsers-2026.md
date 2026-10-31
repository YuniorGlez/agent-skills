# Navegadores agénticos / browser automation para agentes — paisaje agosto 2026

Verificado el 8-ago-2026 con la API de GitHub (stars/pushed/license) + READMEs.
Útil para elegir el stack de navegación web de un agente (p.ej. "Guille").

## Categoría A — Frameworks/SDK (los integras TÚ en el agente)

| Proyecto | Stars | Lang | Licencia | Para qué |
|---|---|---|---|---|
| browser-use/browser-use | 108.2k | Python | MIT | El estándar de facto. SDK agent-first, 89% WebVoyager, MCP incluido (com.browser-use/browser-use). Activo. |
| vercel-labs/agent-browser | 40.2k | Rust | Apache-2.0 | CLI nativo para agentes, snapshot-based (vista estructurada estable de la página para el LLM, sin CSS selectors frágiles). Instalación: `npm i -g agent-browser` o `brew install agent-browser` + `agent-browser install` (Chrome for Testing). |
| browserbase/stagehand | 23.8k | TS | MIT | SDK act/extract/observe con lenguaje natural + código; local (Playwright) o cloud Browserbase. |
| Skyvern-AI/skyvern | 22.7k | Python | AGPL-3.0 | Vision-first, formularios y flujos multi-paso (legacy). ⚠️ AGPL: obliga a abrir tu código si lo integras — evitar salvo flujos muy específicos. |
| unclecode/crawl4ai | — | Python | — | Crawling LLM-friendly (alternativa de extracción). |

## Categoría B — Navegadores agénticos completos (producto, humano+IA)

- **browseros-ai/BrowserOS** (13.0k⭐, TS, AGPL-3.0, activo): open-source,
  alternativa a ChatGPT Atlas / Perplexity Comet / Dia. 40+ integraciones.
- Comerciales: ChatGPT Atlas, Perplexity Comet, Dia (The Browser Company),
  Sigma Browser.

## Recomendación (caso la agencia: navegación agéntica para un agente propio)

1. Si el agente es un Hermes: Hermes YA trae navegación (Chrome CDP + motor
   Camoufox stealth). El salto de calidad = añadir el **MCP de browser-use**
   (`hermes mcp`) → navegación con el estándar de la industria.
2. Si el agente es un CLI/script propio: **vercel-labs/agent-browser**
   (Rust, Apache-2.0, snapshot-based, pensado para LLMs).
3. Evitar Skyvern (AGPL) salvo formularios legacy; Stagehand si el stack es TS.

## Método de verificación usado (replicable)

```bash
# stars/licencia/actividad en vivo, sin auth:
curl -s "https://api.github.com/repos/<owner>/<repo>" | jq '{full_name, stargazers_count, pushed_at, language, license: .license.spdx_id, description}'
# READMEs raw (evita el extract y el navegador):
curl -s "https://raw.githubusercontent.com/<owner>/<repo>/main/README.md"
```

La búsqueda inicial vía web_search (backend ddgs) + verificación GitHub API =
triangulación suficiente sin navegador.
