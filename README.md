# Agent Skills

Battle-tested skills for AI coding agents (Hermes Agent, Claude Code, Codex): how to drive a
desktop, a browser or a repo, and the working methods around them.
Each skill here was written while doing real work and corrected after the mistakes it records.
Everything is measured: latencies, token costs, error codes.

Habilidades para agentes de IA que salen de trabajo real, no de un tutorial. Cada una incluye lo
que se midió, lo que falló y por qué, con los comandos exactos.

## Qué hay

| Categoría | Skill | Para qué |
|---|---|---|
| `browser/` | **computer-use-desktop** | Operar apps de escritorio por el árbol de accesibilidad: macOS, Windows y Linux; refs estables, verificación y límites reales |
| | **chrome-cdp-access** | Ver y manejar el navegador que el usuario tiene abierto: pestañas, DOM, JS, sesión real |
| | **agent-browser** | Elegir la herramienta de navegación correcta según el trabajo (motor propio, Chrome real, auditoría a11y) |
| | **local-web-tunnel** | Exponer un artefacto local con URL pública, sin desplegar |
| `engineering/` | **third-party-repo-triage** | Auditar repos de terceros antes de adoptarlos: valor, seguridad, telemetría, cadena de suministro |
| | **code-context-tools** | Elegir y medir la herramienta de contexto de código (grep, grafos, recuperadores) |
| | **blockwise-file-authoring** | Escribir ficheros largos por bloques sin que el resultado se corrompa |
| | **to-spec** | Convertir una conversación en una especificación del proyecto |
| | **to-tickets** | Partir una spec en tickets verticales con dependencias |
| | **grilling** | Afilar un plan a base de preguntas incómodas antes de construirlo |
| | **gauntlet-loop** | Bucle de construcción y crítica ciega en vez de una pasada y ya |
| | **accesibilidad-wcag** | Auditar y corregir accesibilidad web WCAG 2.2 AA |
| | **idioma-interfaz-web** | Pasar una interfaz a varios idiomas sin romper el layout |
| `work/` | **web-research** | Investigar en la web con etiquetas de fuente y verificación de afirmaciones |
| | **ocr-and-documents** | Extraer texto de PDFs y escaneos, y decidir cuándo OCR sí y cuándo no |
| | **editar-xlsx-sin-perder-formulas** | Editar un Excel existente conservando fórmulas y estilos |
| | **limpieza-disco-macos** | Auditar qué ocupa el disco en macOS y qué se puede borrar sin riesgo |
| `hermes/` | **handoff** | Compactar una conversación para que otro agente siga el trabajo |
| | **skill-library-sync** | Mantener una biblioteca de skills sincronizada entre varios arneses |
| | **machine-context** | Recoger el contexto de una máquina (hardware, software, red) sin adivinar |

## Cómo se instalan

Cada skill es una carpeta con `SKILL.md` y, si aplica, `references/` y `scripts/`.

**Hermes Agent** — copiar a la biblioteca del perfil:

```bash
cp -R browser/computer-use-desktop ~/.hermes/skills/devops/
```

**Claude Code / Codex** — copiar la carpeta dentro de `.claude/skills/` o `.codex/skills/` del repo
donde vayas a usarla, o a la carpeta global del arnés.

**Cualquier agente** — el `SKILL.md` es Markdown con frontmatter (`name`, `description`). Se puede
pegar tal cual en el contexto o convertirlo en instrucciones.

## Convenciones

- El frontmatter declara `name`, `description` y, cuando aplica, `platforms` y `license`.
- Los `scripts/` funcionan sin dependencias del autor: `python3` o `node` y poco más.
- Los números que aparecen son de una máquina concreta y se dice cuál; no son promesas del fabricante.
- Cada pitfall tiene su síntoma, su causa y la comprobación que lo distingue de otro fallo parecido.

## Licencia

MIT. Ver [LICENSE](LICENSE).
