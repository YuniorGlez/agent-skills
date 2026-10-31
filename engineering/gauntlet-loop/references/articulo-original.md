# Artículo original — "How to Run a Gauntlet Loop"

**Autor:** Matt Shumer (@mattshumer_) · **Fecha:** 27 jul 2026
**URL:** https://somethingbig.ai/gauntlet-loop
**Contexto:** la metodología detrás de "Claude of Duty" (FPS tipo CoD hecho por
Claude Opus 5 desde un único prompt corriendo en Claude Code: ~55.000 líneas de
código + todas las texturas/meshes/animaciones/sonidos generados desde cero, sin
que el autor lo dirigiera). El post original se hizo viral (millones de views),
lo acusaron de fake, publicó el prompt + código (open source), la gente lo
replicó y funcionó.

## Tesis central
> "En vez de dejar que produzca un resultado decente y pare, lo hice seguir
> comparando su trabajo contra un listón mucho más alto. He llamado a esto un
> **Gauntlet Loop**."

Un Gauntlet Loop funciona así:
- Das a un agente lider un **objetivo** y un **ejemplo real de cómo se ve lo
  excelente** (el listón).
- El agente lider decide cómo dividir la meta en las piezas más pequeñas que
  pueden mejorarse por separado.
- Cada pieza tiene su **builder** y un **critic separado con contexto fresco**.
- El builder construye; el critic compara contra el listón de referencia.
- Si el listón gana, el critic explica la brecha más grande y la devuelve al
  builder. Otra ronda. Repetir hasta que el resultado alcance el listón (o el
  usuario decida que está listo).

Aplica a: código, webs, diseño de producto, campañas de marketing, escritura,
investigación, "o casi cualquier cosa donde la salida se pueda inspeccionar y
mejorar".

## Los 7 principios (resumen operativo)
1. **Usa un agente real** (Claude Code / Codex o harness agéntico que permita
   abrir archivos, ejecutar, ver screenshots, spawnear subagentes). No sirve
   pegarlo en un chat normal. Su default: Claude Code + Opus 5, subagentes con
   su propio contexto limpio. Codex bueno para backend / criticar visual, más
   débil creando lo visual. Para runs serios: activar `ultracode` (`/effort`).
2. **Objetivo, no implementación**: no prescribas arquitectura ni pasos. El
   prompt original no listaba sistemas ni explicaba el renderer. "Dale el
   destino, deja que elija la ruta."
3. **Un listón real**: "hazlo increíble" / "production-ready" / "sigue
   mejorando" NO son listones. Necesita algo concreto e inspeccionable:
   - Juego → screenshots reales de Call of Duty (comparar side-by-side).
   - Web → las mejores webs reales de la categoría.
   - Escritura → párrafos de referencia al nivel de claridad deseado (ej. Paul
     Graham), no para copiar la voz sino para que el critic pregunte "¿mi
     párrafo es al menos igual de claro?".
   - Backend → suite de tests, target de latencia, test de recuperación,
     revisión de seguridad, o implementación de referencia.
   - El listón NO necesita ser realista/alcanzable: dio dirección y evitó que
     parara en "muy bueno para IA". Su juego no superó a CoD; lo paró mientras
     aún mejoraba.
   - Si no sabes cuál es el listón: que encontrarlo sea parte de la tarea.
     "Encuentra la medida concreta que juegue el mismo papel que los screenshots
     de CoD para esta tarea. Explica por qué es buen listón y juzga cada ronda
     contra él."
4. **Que el agente divida el trabajo**: el lead descompone en piezas
   independientes y juzgables ("haz que este árbol compita con este del ref")
   en vez de "mejora el juego" (demasiado vago). Puede correr piezas en
   paralelo.
5. **Que el builder nunca se autoevalúe**: el builder recuerda sus decisiones y
   es experto en justificarlas como "razonables". No quieres razonable, quieres
   juicio independiente. Spawnea un critic fresco con (objetivo, listón, reglas,
   artefacto) pero SIN el historial/explicaciones del builder. El critic se
   comporta como A/B tester: ve obra y referencia sin saber cuál es cuál, elige
   el mejor, y si pierde la obra identifica la brecha más grande. El critic debe
   inspeccionar la COSA REAL (píxeles, producto corriendo, página renderizada,
   tests), nunca un resumen del builder.
6. **Déjalo seguir**: no digas "haz 3 rondas y para". Sin ronda final
   arbitraria (`/loop` en Claude Code). Con un listón alto casi siempre queda
   otra brecha. Para cuando te guste el resultado / las mejoras sean marginales /
   se agote tu presupuesto.
7. **Vigílalo sin interrumpirlo** (bonus): dile que cree una página HTML en vivo
   o un workbench.md que actualice con el progreso (screenshots, videos, drafts,
   tests). La ves desde el móvil y solo entras cuando quieres parar.

## Smoothing pass (opcional)
Al final de cada ola grande, un agente fresco inspecciona el resultado completo y
lo "pule": no rediseña, arregla conflictos entre piezas y hace que el todo se
sienta "una sola cosa" y no una colección de partes mejoradas por separado.
Útil pero no es el núcleo. El núcleo: **split, build, judge, repeat**.

## "Build your own Gauntlet Loop prompt" (meta-prompt DIY)
Pega esto en un modelo fuerte junto a tu objetivo; deja que ELIJA el listón y
escriba el prompt final; luego ejecútalo en Claude Code o Codex:

> I want to run a Gauntlet Loop for this goal: [GOAL]
> Possible references or quality bars: [OPTIONAL REFERENCES]
> Choose the strongest concrete bar that an agent can actually inspect and
> compare its work against. If I have not supplied one, propose a useful comp or
> measurement that plays the same role for this task that real Call of Duty
> screenshots played for Matt Shumer's Claude of Duty game (read the prompt:
> github.com/mshumer/Claude-of-Duty/blob/main/prompt.md). Explain the bar in one
> sentence.
> Then write a short prompt for Claude Code or Codex in the style of Matt's
> (minimal is better: we want the agent to decide the specifics!). Give the lead
> agent the goal and the bar, but let it choose the approach. Tell it to divide
> the goal into the smallest pieces that can be improved and judged
> independently. For each important piece, fan out a builder and a separate
> critic with fresh context. Each critic must inspect the real output, compare it
> directly with the bar — using a blind A/B comparison when possible — identify
> the biggest remaining gap, and send it back for another round. Keep looping
> until our output wins or I stop the run. Have the lead agent maintain a simple
> live progress page. Use subagents and ultracode. Do not prescribe the
> architecture, exact decomposition, or a fixed number of rounds. Keep the final
> prompt short, just like Matt's.

También existe un "prompt generator" gratuito (en su web / algo.big) que
escribe el prompt listo para pegar a partir de lo que quieras construir.

## Cierre del autor (resumen del método en 5 líneas)
> "Establece un objetivo ambicioso. Dale al agente un listón que no pueda
> esquivar hablando. Deja que decida cómo dividir el trabajo. Mete cada pieza por
> un crítico independiente. Y mantén los bucles corriendo más tiempo del que casi
> cualquiera mantendría."
