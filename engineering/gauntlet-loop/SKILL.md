---
name: gauntlet-loop
description: >
  SINLIMITE: Gauntlet Loop mode, split-build-judge-repeat.
tags: [agents, prompting, quality, loop, sinlimite]
---

# Gauntlet Loop (palabra secreta: `SINLIMITE`)

## Qué es
Un método de prompting para **agentes reales** (Claude Code, Codex, o aquí en
Hermes con `delegate_task`). En vez de pedir "hazlo bien" y que pare, se mete el
trabajo en un **bucle sin ronda final arbitraria**:

**split → build → judge → repeat**

Cada pieza se construye, se compara **a ciegas (A/B)** contra un **listón
concreto e inspeccionable**, y si el listón gana, el crítico explica la mayor
brecha e itera hasta que el resultado gane o el usuario decida parar.

Se hizo viral por **Claude of Duty** (Matt Shumer, jul 2026): un FPS tipo CoD
completo (~55.000 líneas + assets) generado por Claude Opus 5 desde un único
prompt corriendo en Claude Code.

## Trigger (palabra secreta)
- **El usuario dice `SINLIMITE`** (o una variante: "vamos a hacer un gauntlet",
  "mode SINLIMITE", "sinlimite", "mete esto en un gauntlet loop")
- O pide un build/artefacto "con calidad implacable", "a nivel de best-in-class",
  "comparado con los mejores reales", "que no pare hasta que sea top".

Al trigger: **responde entrando en modo SINLIMITE**, reconoce la palabra, resume
el objetivo y el listón, y ejecuta el flujo de abajo. TODO el trabajo se hace
dentro del hilo/chat actual; no mandar a otro sitio.

## Diferencias clave con SINPRISA
| | SINPRISA | SINLIMITE (Gauntlet Loop) |
|---|---|---|
| Foco | 5 Whys, calidad de proceso, no apresurarse | Calidad del artefacto por iteración implacable |
| Mecánica | Pensar antes de ejecutar, proponer extras | Builder vs Critic separados, A/B a ciegas, loop |
| Rondas | Las que requiera el razonamiento | Sin tope fijo: hasta que gane o el usuario pare |
| Uso típico | Decisiones, análisis, propuestas de valor | Builds autonómicos (juegos, webs, CAD, diseño, escritura) |

## Requisitos (no es opcional)
1. **Agente real** con herramientas (aquí: `delegate_task`, `execute_code`,
   `terminal`, `browser`). NO vale copiar el prompt a un chat normal.
2. **Objetivo, no implementación**: dar el QUÉ, no el CÓMO. El agente lider decide
   arquitectura y descomposición.
3. **Listón concreto e inspeccionable**: un comparador real (screenshots de los
   mejores, suite de tests, targets de latencia, texto de referencia, producto
   best-in-class). "Hazlo increíble" NO es un listón. Si no hay listón, la fase 1
   del loop es definirlo.
4. **Builder ≠ Critic**: el crítico es un subagente/task separado con contexto
   fresco. NUNCA deja que el constructor se autoevalúe (siempre se justifica a sí
   mismo como "razonable").
5. **A/B a ciegas**: el crítico ve obra vs listón sin saber cuál es cuál y elige
   el mejor. Si pierde la obra, identifica la brecha más grande y la devuelve.
6. **Sin ronda final arbitraria**: repetir hasta que gane o el usuario pare.

## Cómo lo ejecuto en Hermes (flujo operativo)
1. **Definir objetivo + listón** (preguntar al usuario si hace falta: referencias,
   URLs, tests, productos de referencia).
2. **Fase 0 (si no hay listón claro)**: task de definición — "encuentra la medida
   o comparación concreta que juegue el mismo papel que los screenshots de CoD para
   esta tarea y explica por qué es buen listón".
3. **Split**: dejar que el agente lider descomponga en las piezas más pequeñas
   mejorables por separado (no imponer la descomposición).
4. **Loop por pieza** con `delegate_task` (batch): un task = builder, otro =
   critic con contexto fresco; el critic devuelve la brecha; re-delegar hasta que
   el critic diga que gana (o tope de presupuesto acordado).
5. **Smoothing pass** al final de cada ola (opcional): task fresco que reconcilia
   las piezas y las hace sentir "una sola cosa".
6. **Progreso visible**: mantener un workbench.md o página que se actualiza, para
   que el operador lo mire sin interrumpir.
7. Junto a la entrega final: reportar QUÉ se hizo por ronda, cuántas rondas, y el
   veredicto del crítico (no solo "está hecho").

## Buenas prácticas
- Listón alto de forma deliberada, incluso inalcanzable: da dirección y evita que
  pare en "decente para IA".
- Inspeccionar el artefacto REAL (píxeles, página render, tests), nunca un resumen
  del builder.
- Decidir el tope de coste/tiempo ANTES de empezar (estos loops queman tokens).
- Si el resultado es un juego/code autocontenido: más apropiado. Código de
  producción acoplado y complejo: ojo, ver pitfalls.

## Pitfalls (aprendidos de la comunidad, jul 2026)
- **Coste/tokens altos**: levelsio quemó $500-900 por run y acabó con "código no
  performante y caos". Acordar presupuesto antes.
- **Overload cognitivo**: a las 2h "se ve increíble... hasta que lo miras de
  cerca". Validar con humanos en la fase final.
- **Agente fuera de control**: puede reescribir muchos archivos sin permiso.
  Trabajar en rama/copia, con checkpoints y kill switch claro.
- **Confundir el método con "solo un prompt largo"**: la magia es la arquitectura
  (contextos limpios + critics separados + A/B), no el texto.
- El crítico NO debe ver el historial ni la explicación del builder.

## Pre-check estructural antes del crítico (barato)
Para builds de landing/página: pasar los screenshots por `scripts/precheck.py`
(default **google/gemini-3.7-flash** vía OpenRouter, ~$0.0007/pregunta) ANTES de la ronda del crítico
estético. Detecta rotura estructural (texto solapado, elementos descolocados, CTA ausente) y devuelve
exit 1 → corregir primero y no quemar tokens del crítico en un build roto. El crítico estético sigue
siendo qwen3.8-max (gemini flash NO sabe localizar CTAs: 0/9 de acierto en grounding, 13-ago-2026).
NO usar LFM2.5-VL-3B local para esto (descartado 13-ago-2026: no corre en MLX ni GGUF hoy).
Sin screenshots (p.ej. texto/CSV), omitir este paso.

## Referencias
- `references/articulo-original.md` — Resumen del artículo de Matt Shumer
  "How to Run a Gauntlet Loop" (somethingbig.ai/gauntlet-loop).
- `references/prompt-original-y-metaprompt.md` — Prompt verbatim de Claude of Duty
  + plantilla meta-prompt DIY + generator.
- `references/ejemplos-y-criticas.md` — Ejemplos reales de X y críticas
  (levelsio, DannyLimanseta, killix) para contexto equilibrado.
