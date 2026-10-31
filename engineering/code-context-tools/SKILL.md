---
name: code-context-tools
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [code-context, repo-map, mcp, agents, benchmarking]
description: Elige herramienta de contexto de código y mídela.
---

# Herramientas de contexto para agentes de código

## Cuando usar

- El usuario pregunta qué herramienta usar para dar contexto del repo a un agente.
- Hay que decidir entre repo-map, grafo, búsqueda semántica o recuperador.
- Se va a medir o comparar cualquier herramienta de este tipo.

## Reglas duras (medidas 3-4 oct 2026, banco de 62-86 turnos reales)

1. **Antes de medir una herramienta, ejecuta su `doctor` y comprueba que está COMPLETA.**
   Tres de mis cifras salieron mal por medir sistemas a medio configurar: Graft sin el grafo
   construido (`ask` devuelve `(empty)` con **exit 0**), GitNexus sin la extensión VECTOR
   (`exact-scan only`) y jevgrep sobre 64 casos en vez de 86.
2. **No compares corridas parciales entre sí.** En un banco que crece mientras mides, cualquier
   media se contamina. Espera a que los dos lados tengan el mismo `n` y los mismos casos.
3. **Pregunta por el `n` siempre.** Un R@5 sin su `n` no es un dato.

## Qué es cada herramienta (no compiten, se reparten el trabajo)

| Necesidad | Herramienta | Por qué |
|---|---|---|
| Orientación al empezar | `graft map` | 456 tokens, 0,4 s, sin clave. Clusters, hubs, hotspots con `file:line` |
| Qué rompo si toco esto | **GitNexus `impact`** | Da **nivel de riesgo** + flujos afectados + conteo por profundidad. Único |
| Vista 360 de un símbolo | GitNexus `context` | Incoming/outgoing con `epistemic: "exact"` |
| Quién llama a X | `graft callers` | 94 % de ahorro de tokens, con la línea exacta |
| Blast radius para el PR | `graft blast` | Mermaid, pensado para CI |
| Buscar por comportamiento | **jevgrep** (0,231) o semble (0,179) | ver abajo |
| Buscar literal | `tgrep` | El 75 % de las búsquedas reales |

## Lo que NO hay que usar como recuperador

| Herramienta | R@5 (no literal) | Qué es en realidad |
|---|---|---|
| Recencia intra-sesión | **0,240** | La línea base. **Bate a todos los recuperadores** |
| jevgrep | 0,231 | El mejor recuperador, pero **falla en el 54 % de los casos** y llega a 286 s |
| Índice propio + Jev | 0,189 | Descartado: no bate a la recencia y cuesta mantenerlo |
| semble | 0,179 | El más fiable (12 % de fallos) y entrega código literal |
| Graft `ask` | 0,094 | **Léxico**, lo dice él mismo |
| GitNexus `query` | 0,008 | **Estructural**: busca flujos, no ficheros |
| *Techo@5 perfecto* | *0,877* | Ni el mejor se acerca |

## El hallazgo que decide

**El agente ya encuentra.** Mediana de **0 lecturas antes** del primer fichero que acaba editando; acierta a
la primera en el **61 %** de los turnos que no nombran nada. Lo que le cuesta es **entender** después (13
ficheros de media por cambio). **Ningún recuperador resuelve eso.**

**El turno en frío no lo resuelve ninguna herramienta**: lo mejor acierta 1 de cada 12 (0,08). Es un
problema de **memoria** (lo que hizo el agente en sesiones anteriores), no de recuperación.

## Instalación en un Mac (trampas reales)

```bash
# Graft: bun bloquea postinstall por seguridad y tree-sitter-kotlin NO trae prebuilds
bun add @nanonets/graft && bun pm trust --all
# si su CLI muere con "No native build was found", compilar a mano:
cd node_modules/tree-sitter-kotlin && npx node-gyp rebuild

# GitNexus: saltar los grammars opcionales evita necesitar toolchain de C++
export GITNEXUS_SKIP_OPTIONAL_GRAMMARS=1
bun add -g gitnexus@latest
```

### Trampas de GitNexus

- **`analyze --embeddings` toma un NÚMERO, no una ruta.** `analyze --embeddings .` falla con
  `expects a non-negative integer (got ".")` y deja la extensión VECTOR sin instalar. Sin valor = default.
- **La extensión VECTOR es lo que activa la semántica.** Sin ella: `Semantic support: exact-scan only`.
  Con ella: `vector-index capable`. Se instala con `GITNEXUS_LBUG_EXTENSION_INSTALL=auto`.
- **El índice se marca `stale` si cambia el binario de node.** Ejecuta `analyze` con el **mismo node**
  que lo creó (aquí: nvm v24 vs homebrew v26) o quedará stale en bucle.
- **Indexado incremental: ~3 s** tras el primero. El primero, 15-62 s.

### Trampas de Graft

- **`graft ask` devuelve `(empty)` con exit 0** si el repo no tiene grafo. Cero silencioso: parece
  «no hay nada» cuando es «no lo he construido». Crea `graft/` vacío, así que comprobar que el
  directorio existe **no basta**: hay que contar los `.md`.
- **No escala a directorios contenedores** (`~`, `~/.hermes`): `build` se rinde. Dale la **raíz del proyecto**.
- **`graft init` sin flags escribe en configs de TODOS los repos** (`~/.codex/config.toml`,
  `~/.claude/settings.json`). Usa `--agents hermes --no-global`: solo toca el `AGENTS.md` del repo.

## Leer la salida de GitNexus desde shell (lección dura: 5 intentos fallidos)

**No metas la salida del CLI en un `python3 -c "json.load(...)"` por tubería.** El CLI escribe líneas de
log JSON (`{"level":30,...}`) y **el parser recibe el log en vez de la respuesta**. Cinco intentos distintos
de un script de verificación en Python fallaron por esto. Lo que sí funciona, y es más corto:

```sh
# BIEN: regex con rg, sin parser
ctx=$(gitnexus context "$sym" 2>/dev/null | rg -o '"status": "[a-z]+"' | head -1 | sed 's/.*: "//;s/"//')
risk=$(gitnexus impact "$sym" 2>/dev/null | rg -o '"risk": "[A-Z]+"' | head -1 | sed 's/.*: "//;s/"//')
```

- Redirige **`2>/dev/null`**: el log puede ir por stderr o mezclado.
- **La respuesta limpia sí parsea directo** con `json.loads` si la capturas con `subprocess` (sin tubería):
  el ruido aparece al pasar por shell. No asumas que hay logs; comprueba la salida cruda antes.
- **No dejes un script de verificación averiado en el laboratorio.** Si tras 3 intentos no funciona, retíralo
  y verifica a mano: un script roto es peor que ninguno, porque produce ceros que parecen datos.

### Verificar GitNexus sin falsos negativos

**Usa un símbolo REAL, extraído del código del propio repo.** Nombres genéricos (`GET`, `POST`, `login`,
`main`) dan `ambiguous` — pide el UID, correctamente — o no existen, y un test con basura produce
«todo falla» en los 11 repos (medido).

```sh
sym=$(rg -o -N 'export (async )?function ([A-Za-z_]\w*)' -r '$2' --no-filename -g '*.ts' src | sort -u | head -1)
```

## Reglas de seguridad al cablear una herramienta en repos del usuario

1. **`--dry-run` primero** y leer qué ficheros tocaría. Descartar lo que salga del repo.
2. **Solo lo que se pidió**: `--agents hermes --no-global` en vez del init completo.
3. **Backup** de todo fichero que se modifique (`AGENTS.md.bak-<herramienta>-<fecha>`).
4. **Verificar con `git status`** que no se tocó ningún fichero de código, y separar lo propio de lo
   que el usuario ya tenía sin commitear.
5. **No commitear** sin su OK; si se commitea, con rutas explícitas, nunca `git add .`.

## Banco de prueba reutilizable

`~/projects/<laboratorio>/` — 292 turnos reales con secuencia ordenada de `read`/`edit`,
verdad observada (los ficheros que el agente editó de verdad), y las mediciones de cada sistema.
Scripts: `bench_external.py` (mide cualquier herramienta), `extract_seq.py`, `probe_graft.py`.
