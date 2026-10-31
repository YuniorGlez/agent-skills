# Ejemplos reales y críticas (X, a 5 ago 2026)

## Ejemplos / pruebas que funcionaron (más allá de Claude of Duty)
- **@kyel_ok**: "Opus 5 oneshotted one of the most popular games of 2026 using
  Three.js and @MattShumer_'s gauntlet loop. Still rough around the edges..."
  (~553+ likes en el hilo de Shumer).
- **@earthtojake**: F1 car con text-to-CAD + gauntlet loop, un solo prompt →
  STEP file con **850+ partes** (otro hilo: 1500+ partes incl. suspensión).
  Google: "opus 5 ultracode with text-to-cad and a gauntlet loop".
- **@0xRishi**: build "en unos días con Opus 5 & gauntlet loop, todo web native".
- **@majidmanzarpour, @moridinamael, @suriadesign, @markgadala, @0xRishi**:
  más juegos publicados en X.
- Juegos jugables citados en el artículo: Kart Royale, Der Koloss (co-op zombie
  4 jugadores), Pastel Nuketown, Dream Logic, Dungeon Crawler Carnage.
- **@prasenx**: aplicación de gauntlet loops que a Shumer le gustó tanto que
  pidió usarla para no gastar tokens 😅.
- **@easys_arq**: "Opus 5 es increíble, pero esto demuestra que el prompting es
  todo. Corrí el prompt de gauntlet de @MattShumer_ en mi juego de Spiderman..."
- Shumer parando a enseñar a Claude a usar Unreal Engine: "cerca del punto de
  poder correr Gauntlet Loops para construir juegos reales en UE".
- Otro usuario en "day 14" de un space game: modelos pasados por un "modified
  gauntlet loop" para generar vehículos de terreno (GPT 5.6 Sol y K3).

## Críticas / contras (importante tener el equilibrio)
- **@levelsio (Pieter Levels)**, 5 ago 2026 (813 likes):
  "Every time I do a Gauntlet Loop I end up with a total mess and chaos of
  unperformant code and too many things happening and nothing works properly.
  And I burn $500. I have to clean everything up manually and get back to what I
  had. The only way for me to AI code is just step by step." → su reto va de
  perder el control y el coste.
- **@DannyLimanseta**, 5 ago 2026 (152 likes):
  "The problem with the Gauntlet Loop approach is the cognitive overload that
  overwhelms the builder. Imagine this: you set up an amazing prompt and send
  your agent off to build the game all in one go. 2 hours later you have a
  playable game. It looks amazing at first glance..." → parece increíble hasta
  que lo inspeccionas de cerca.
- **@killix**, 5 ago 2026: "After @levelsio torched $900 on a gauntlet loop and
  binned 95%, yesterday I caught my own agent rewriting 17 files while I was
  out. No PID, no log, no kill switch. I now wrap every agent as a shell job."
  → riesgo operativo: agente tocando cosas sin supervisión ni kill switch.
- **@JamesSampica**: "a gauntlet loop is just an agent loop in the category of
  vibecode slop" → escepticismo de que sea novedoso.
- **@juminoz**: "don't use it for anything serious. Even with the gauntlet loop
  can't help all the time. What we are seeing on X are being masked coz it
  really needs help. It's a waste of time." → hay resultados cherry-picked.
- **@mjovanovictech**: "what in the world is a Gauntlet Loop" → síntoma de que
  el término se está difundiendo como meme / buzzword.

## Síntesis para decidir cuándo usarlo
**A favor:** resultados espectaculares para builds creativos y autocontenidos
(juegos, CAD, webs, diseño) donde la calidad se puede ver/comparar contra un
listón real, y donde hay contexto y presupuesto.

**En contra:** coste alto en tokens; riesgo de caos/código no mantenible cuando
se escala sin supervisión; "parece espectacular de lejos, se cae de cerca"
(validar con humanos); peligro de agente tocando archivos sin kill switch.
Para código de producción acoplado y crítico, la comunidad (levelsio) recomienda
paso a paso en vez de loop autonómico.

**Recomendación práctica (síntesis):** usar el patrón builder/critic + listón
concreto + A/B a ciegas como mentalidad siempre que se pueda; reservar el loop
autonómico completo (SINLIMITE) para piezas autocontenidas, con presupuesto
acordado y supervisión del progreso en vivo.
