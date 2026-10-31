# Prompts de referencia (verbatim)

## 1) El prompt original de Claude of Duty (EL prompt completo)

Repo open source: https://github.com/mshumer/Claude-of-Duty (prompt.md)

```
I want you to build a first-person shooter at the level of the most recent
Call of Duty games. It should be utterly perfect, visually beautiful, with
every single thing done at AAA quality—from textures to physics to anything
you could think of.

Fan out sub-agents and have sub-agents tackle each one individually so that
the game is utterly perfect. You should /loop on each item and have a separate
sub-agent check it visually to ensure it looks triple A. That separate
sub-agent should be a really harsh critic, and if it doesn't look triple A, it
should keep going.

Don't stop until each sub-agent is utterly wowed with the quality when compared
with the actual Call of Duty game. It should literally compare them side by
side blind and say which one looks better. Do this in ThreeJS. /loop until it's
utterly perfect. Fan out sub-agents and ultracode.
```

**Análisis de por qué funciona (para no perderlo al adaptarlo):**
- "at the level of the most recent Call of Duty games" = **listón**, no "haz un FPS".
- "Fan out sub-agents" + "tackle each one individually" = **split**.
- "separate sub-agent check it visually... really harsh critic" = **builder ≠ critic**.
- "compare them side by side blind and say which one looks better" = **A/B a ciegas**.
- "/loop until it's utterly perfect" = **sin ronda final arbitraria**.
- "ultracode" = **presupuesto/modo de mayor esfuerzo**.

## 2) Meta-prompt DIY (para generar TU prompt Gauntlet Loop)

Pásalo a un modelo fuerte con tu [GOAL] y referencias opcionales; que él decida
el listón y escriba el prompt corto final para Claude Code/Codex.

> I want to run a Gauntlet Loop for this goal: [GOAL]
> Possible references or quality bars: [OPTIONAL REFERENCES]
> Choose the strongest concrete bar that an agent can actually inspect and
> compare its work against. If I have not supplied one, propose a useful comp or
> measurement that plays the same role for this task that real Call of Duty
> screenshots played for Matt Shumer's Claude of Duty game (read the prompt:
> https://github.com/mshumer/Claude-of-Duty/blob/main/prompt.md). Explain the
> bar in one sentence.
> Then write a short prompt for Claude Code or Codex in the style of Matt's
> prompt (minimal is better here, we want the agent to decide the specifics!).
> Give the lead agent the goal and the bar, but let it choose the approach. Tell
> it to divide the goal into the smallest pieces that can be improved and judged
> independently. For each important piece, it should fan out a builder and a
> separate critic with fresh context. Each critic must inspect the real output,
> compare it directly with the bar—using a blind A/B comparison when possible—
> identify the biggest remaining gap, and send it back for another round. Keep
> looping until our output wins or I stop the run. Have the lead agent maintain
> a simple live progress page that shows the work evolving over time. Have it
> use subagents and ultracode. Do not prescribe the architecture, exact
> decomposition, or a fixed number of rounds. Keep the final prompt short, just
> like Matt's.

## 3) Prompts generados (adaptaciones probadas por la comunidad)
- Juegos (FPS, kart, dungeon, zombie co-op): mismo patrón + "comparar contra el
  juego X real, side by side a ciegas", + "fan out", + "ultracode".
- CAD / ingeniería: "diseña [pieza] con text-to-CAD; compara contra fotos/render
  de referencia reales; critica visualmente cada parte; loop hasta que gane"
  (ej. F1 car → STEP file con 850+ partes, 1 solo prompt, Opus 5).
- Artículos/escritura: "cada párrafo debe ser al menos tan claro como [referencia
  de Paul Graham]; crítico independiente compara a ciegas; iterar".
- Backend: listón = suite de tests / target de latencia / security review en vez
  de comparación visual.

## Nota de coste
Runs serios con ultracode + muchos subagentes pueden quemar cientos de dólares en
tokens (levelsio reportó $500-900/run). ACORDAR PRESUPUESTO ANTES. Decidir
también el kill switch: cuándo y cómo se para el run.
