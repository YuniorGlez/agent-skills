---
name: grilling
description: Grill al usuario para afilar un plan o decisión.
---

# Grilling — afilar un plan con preguntas

Entrevista al usuario implacablemente hasta alcanzar un entendimiento compartido. Modela el plan como un **árbol de diseño**: cada decisión se ramifica en las decisiones que cuelgan de ella.

## Cómo funciona

Trabaja el árbol en **rondas**. La **frontera** es el conjunto de decisiones cuyos prerrequisitos ya están resueltos — las preguntas que puedes hacer *ahora* sin adivinar respuestas que aún no has oído. Pregunta toda la frontera en una sola ronda: numera cada pregunta y da tu respuesta recomendada. Espera las respuestas del usuario antes de la siguiente ronda.

## Formato de cada pregunta

```
❓ **Q1** - **<título de la pregunta>**: <cuerpo de la pregunta, puede ser multi-párrafo, con opciones>

➡️ <tu respuesta recomendada>
```

## Reglas

1. **Toda la frontera en una ronda.** Las respuestas del usuario remodelan el árbol: las decisiones resueltas empujan la frontera hacia afuera y desbloquean preguntas que dependían de ellas. Recalcula la frontera y haz la siguiente ronda.
2. **No mezclar dependencias.** Una pregunta cuya respuesta depende de otra pregunta aún abierta en esta ronda pertenece a una ronda *posterior*, no a esta.
3. **Los hechos son trabajo tuyo, nunca del usuario.** Si una pregunta de la frontera necesita un hecho del entorno (filesystem, herramientas, código), búscalo tú (explora, usa terminal, o lanza un subagente con delegate_task) — no preguntes nada que puedas averiguar. No te bloquees: una exploración en curso es un prerrequisito sin resolver, así que solo esperan las preguntas que dependen de ella — pregunta el resto de la frontera ahora.
4. **Las decisiones son del usuario.** Pon cada decisión ante él y espera. No decidas por él.
5. **Criterio de fin:** la sesión termina cuando la frontera está vacía — cada rama del árbol visitada, nada asumido en silencio.
6. **No actuar hasta confirmar.** No empieces a ejecutar el plan hasta que el usuario confirme que habéis alcanzado un entendimiento compartido.

## Trampas

- **No usar `clarify` para rondas múltiples** — `clarify` es una sola pregunta; para una ronda de la frontera presenta todas las preguntas numeradas en un mensaje y espera la respuesta.
- **No preguntar hechos** (versiones, rutas, config) — se miran, no se preguntan.
- **No hacer preguntas vagas tipo "¿algo más?"** — cada pregunta debe ofrecer opciones concretas o un recomendado.
- **No preguntar de una en una** cuando la frontera tiene varias decisiones independientes: eso multiplica rondas y frustra.

## Verificación

- [ ] ¿Cada pregunta de la última ronda tenía respuesta recomendada?
- [ ] ¿La frontera está vacía (no quedan decisiones sin visitar)?
- [ ] ¿El usuario confirmó explícitamente el entendimiento compartido?
