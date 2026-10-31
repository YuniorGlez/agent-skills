---
name: to-tickets
description: Divide un plan o spec en tickets verticales con bloqueos.
---

# To Tickets — de spec a tickets verticales

Descompón un plan, spec o conversación en un conjunto de **tickets** — slices verticales tipo *tracer bullet*, cada uno declarando los tickets que lo **bloquean**.

## Proceso

### 1. Reúne contexto
Trabaja desde lo que ya haya en la conversación. Si el usuario pasa una referencia (ruta de spec, número/URL de issue), léela completa (cuerpo y comentarios).

### 2. Explora el codebase (opcional)
Si no lo has explorado ya, hazlo para entender el estado actual del código. Los títulos y descripciones de los tickets deben usar el vocabulario del glosario del proyecto, y respetar los ADRs de la zona.

Busca oportunidades de **prefactorizar** para facilitar la implementación: "Haz el cambio fácil, luego haz el cambio fácil" (Kent Beck).

### 3. Redacta slices verticales
Descompón el trabajo en tickets tipo *tracer bullet*:

- Cada slice corta un camino **estrecho pero COMPLETO** a través de todas las capas (schema, API, UI, tests) — vertical, NO un slice horizontal de una sola capa.
- Un slice completado es **demoable o verificable por sí mismo**.
- Cada slice cabe en **una sola ventana de contexto fresca**.
- Cualquier prefactoring va primero.

Da a cada ticket sus **aristas de bloqueo** — los otros tickets que deben completarse antes de que pueda empezar. Un ticket sin bloqueadores puede empezar de inmediato.

**Excepción — refactors anchos:** un refactor ancho es un cambio mecánico (renombrar columna, re-tipear símbolo compartido) cuyo radio de explosión se extiende por todo el codebase, así que una sola edición rompe miles de call sites y ningún slice vertical puede quedar verde. No lo fuerces a tracer bullet: secuéncialo como **expand–contract**. Primero expande: añade la forma nueva junto a la vieja sin romper nada. Luego migra los call sites en lotes dimensionados por radio de explosión (por paquete, por directorio), cada lote su propio ticket bloqueado por el expand, manteniendo CI verde lote a lote porque la forma vieja sigue existiendo. Finalmente contrae: elimina la forma vieja cuando no quede ningún caller, en un ticket bloqueado por todos los lotes de migración.

### 4. Interroga al usuario
Presenta la descomposición propuesta como lista numerada. Para cada ticket muestra:
- **Título**: nombre corto y descriptivo
- **Bloqueado por**: qué otros tickets deben completarse antes
- **Qué entrega**: el comportamiento end-to-end que este ticket hace funcionar

Pregunta al usuario:
- ¿La granularidad se siente bien? (¿demasiado gruesa / demasiado fina?)
- ¿Las aristas de bloqueo son correctas — cada ticket solo depende de tickets que de verdad lo gatean?
- ¿Hay que fusionar o dividir algún ticket?

Itera hasta que el usuario apruebe la descomposición.

### 5. Publica los tickets
- **Archivos locales** → un archivo por ticket en `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numerados de `01` en orden de dependencias (bloqueadores primero). El campo "Bloqueado por" lista los números/títulos de los que depende. Un ticket por archivo, nunca un archivo combinado.
- **GitHub u otro tracker real** → publica un issue por ticket en orden de dependencias (bloqueadores primero) para que las aristas puedan referenciar IDs reales. Usa la relación nativa de bloqueo/sub-issue si existe; si no, pon el "Bloqueado por" con referencia a los issues bloqueantes. Aplica la etiqueta `ready-for-agent` salvo indicación contraria — los tickets son agarrables por agentes por construcción.

Trabaja la **frontera**: cualquier ticket cuyos bloqueadores estén todos hechos. En una cadena puramente lineal, eso significa de arriba a abajo.

**NO cierres ni modifiques el issue padre.**

## Plantilla de ticket local

```markdown
# <NN> — <Título del ticket>

**Qué construir:** el comportamiento end-to-end que este ticket hace funcionar,
desde la perspectiva del usuario — no una lista de implementación capa por capa.

**Bloqueado por:** números/títulos de los tickets que lo gatean, o "None — puede empezar de inmediato".

**Estado:** ready-for-agent

- [ ] Criterio de aceptación 1
- [ ] Criterio de aceptación 2
```

En cualquiera de las dos formas, evita rutas de archivo y snippets de código — se quedan obsoletos rápido. Excepción: si un prototipo produjo un snippet que codifica una decisión con más precisión que la prosa, inclúyelo y anota brevemente que vino de un prototipo.

## Verificación

- [ ] ¿Cada ticket es vertical (atraviesa todas las capas) y demoable por sí mismo?
- [ ] ¿Cada ticket cabe en una ventana de contexto fresca?
- [ ] ¿Las aristas de bloqueo están declaradas y aprobadas por el usuario?
- [ ] ¿Refactors anchos secuenciados como expand–contract?
- [ ] ¿Tickets publicados en orden de dependencias (bloqueadores primero)?
- [ ] ¿El issue padre no ha sido tocado?
