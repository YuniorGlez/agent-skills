---
name: to-spec
description: Convierte la conversación actual en una spec del proyecto.
---

# To Spec — de conversación a spec

Toma el contexto de la conversación actual y el conocimiento del codebase y produce una spec. **NO entrevistes al usuario** — sintetiza lo que ya sabes.

## Proceso

1. **Explora el repo** para entender el estado actual del código, si no lo has hecho ya. Usa el vocabulario del glosario del proyecto (lenguaje ubicuo) en toda la spec, y respeta los ADRs de la zona que toques.

2. **Esboza las costuras de testeo** (*seams*) donde vas a testear la feature:
   - Prefiere costuras existentes a nuevas.
   - Usa la costura más alta posible.
   - Si hacen falta costuras nuevas, propónlas en el punto más alto que puedas.
   - Cuantas menos costuras en el codebase, mejor — el número ideal es **una**.
   - **Confirma con el usuario** que estas costuras coinciden con sus expectativas.

3. **Escribe la spec** con la plantilla de abajo y guárdala en `docs/specs/<YYYY-MM-DD>-<slug>.md` (o `.hermes/plans/` si no hay docs/). Si el usuario lo pide, publícala también como issue de GitHub (etiqueta `ready-for-agent`, sin necesidad de triage adicional).

## Plantilla de spec

### Problem Statement

El problema que enfrenta el usuario, desde la perspectiva del usuario.

### Solution

La solución al problema, desde la perspectiva del usuario.

### User Stories

Una lista LARGA y numerada de user stories, cada una en formato:
`Como <actor>, quiero <feature>, para <beneficio>`

Ejemplo: "Como cliente de banca móvil, quiero ver el saldo de mis cuentas, para tomar decisiones informadas sobre mi gasto".

La lista debe ser extremadamente extensa y cubrir todos los aspectos de la feature.

### Implementation Decisions

Lista de decisiones de implementación tomadas, incluyendo:
- Los módulos que se construirán/modificarán
- Las interfaces de esos módulos que cambiarán
- Aclaraciones técnicas del desarrollador
- Decisiones arquitectónicas, cambios de esquema, contratos de API, interacciones específicas

**NO incluir rutas de archivo ni snippets de código** — quedan obsoletos rápido.
Excepción: si un prototipo produjo un snippet que codifica una decisión con más precisión que la prosa (state machine, reducer, schema, forma de tipos), inclúyelo dentro de la decisión relevante y anota brevemente que vino de un prototipo. Recorta a lo esencial de la decisión, no un demo completo.

### Testing Decisions

Lista de decisiones de testing:
- Qué hace un buen test (testear solo comportamiento externo, no detalles de implementación)
- Qué módulos se testearán
- Prior art para los tests (tests similares existentes en el codebase)

### Out of Scope

Descripción de lo que queda fuera del alcance de esta spec.

### Further Notes

Cualquier nota adicional sobre la feature.

## Verificación

- [ ] ¿La spec usa el vocabulario del dominio del proyecto (no inventa sinónimos)?
- [ ] ¿Las user stories cubren todos los aspectos de la feature?
- [ ] ¿Implementation Decisions no contiene rutas de archivo ni snippets (salvo excepción de prototipo)?
- [ ] ¿Las costuras de testeo fueron confirmadas con el usuario?
- [ ] ¿La spec está guardada en el proyecto?
