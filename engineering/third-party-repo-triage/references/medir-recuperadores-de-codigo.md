# Medir un recuperador de código contra trabajo real

Cuando el candidato es un buscador, un indexador o un «mapa del repo» para agentes, su README no
decide. Se mide sobre **turnos reales del usuario**, y la verdad de referencia se **observa**, no
se opina. Esta es la receta y las trampas que costaron rondas.

## 1. Construir la verdad observada de los logs

De dónde salen los turnos, por harness (todos existen en la máquina de el operador):

| Harness | Fichero | Cómo se lee |
|---|---|---|
| DeepSeek Harness | `~/.dsh/sessions/<repo>/<session>/session.vN.jsonl.zstd` | `zstd -d -c`; eventos `tool/call` con `data.name` y `data.arguments` (JSON en string) |
| Hermes | `~/.hermes/state.db` (SQLite) | `sessions.cwd` da el repo; `messages.tool_calls` (JSON) trae `function.name` y `function.arguments.path` |
| Claude Code | `~/.claude/projects/<repo>/<uuid>.jsonl` | eventos `type=user|assistant`; bloques `message.content[]` con `type=tool_use` |
| Codex | `~/.codex/archived_sessions/rollout-*.jsonl` | formato propio, parser aparte |

**La verdad es el par (petición del usuario → ficheros que el agente editó de verdad).** La
petición es el último mensaje de usuario antes del turno; los ficheros son los que aparecen en
una llamada de edición (`Edit`/`Write`/`MultiEdit`/`patch`) mientras el turno está abierto.

**Guarda la SECUENCIA, no solo los conjuntos.** El orden real de `read` y `edit` es lo que permite
medir «cuántas lecturas hizo el agente ANTES de dar con el fichero bueno», que resulta ser la
métrica que decide si un recuperador tiene trabajo o no.

## 2. El estrato que importa, y por qué hay que separarlo

Clasifica cada petición por si el usuario **ya nombró el objetivo**:

- **literal** — el mensaje lleva un fichero con extensión, un término entre backticks/comillas,
  un identificador camelCase/snake_case de 8+ chars, o el nombre de un fichero del repo.
- **no literal** — describe comportamiento sin nombrar nada («arregla la UI de finanzas»).

**Solo el estrato no literal tiene trabajo para un recuperador.** Medido en el corpus real: el
**75 % de las búsquedas son literales** (61 % regex, 15 % símbolo exacto). Ahí la respuesta es
`tgrep`/`rg`, no un modelo.

## 3. Las líneas base, y la que hay que batir primero

La línea base que decide el proyecto es la **recencia intra-sesión** (coste cero, sin modelo):
los ficheros ya tocados en la misma sesión, del más reciente al más antiguo. En la medición real
ganó a todo recuperador que lee código en el estrato no literal.

Añade además: recencia + frecuencia global del repo, BM25 sobre contenido, búsqueda por nombre de
fichero, el candidato, y el mismo índice **sin** el modelo de decisiones (ablación clave: si
empatan, el modelo sobra). Y el **techo@5 = min(5, n_editados) / n_editados**: un recuperador
perfecto tampoco cubre una verdad multi-fichero, así que sin techo no sabes si un 0,46 es bueno.

## 4. Trampas medidas (todas costaron una ronda)

- **Nunca compares corridas con distinto `n`.** Es el error más caro y el más invisible. Los casos
  fáciles entran antes en el banco, así que una media parcial está sesgada por el orden de llegada.
  Antes de publicar una comparación, verifica en código que los dos lados tienen **los mismos casos**
  (intersección por clave estable, no por índice) y el mismo `n`.

- **Un cero silencioso con `exit 0` no es un cero real.** Muchas CLI devuelven «vacío» y salen con
  0 cuando les falta su preparación (índice sin construir, sin credencial). Si un sistema saca 0
  sistemáticamente, comprueba que tenía todo lo que necesita ANTES de creer el número. Un `graft`
  sin grafo responde `(empty)` con exit 0 y parece que la herramienta no funciona.

- **Comprobar que el directorio de caché existe no basta.** Hay herramientas que lo crean vacío.
  Cuenta los ficheros que debería contener (p. ej. los `.md` del índice) antes de asumir que está
  listo.

- **Las herramientas que leen código se comen el presupuesto de estado.** Un índice de 1.000
  ficheros no cabe en el límite de una API de decisión: la llamada falla con 400 y el sistema
  devuelve 0 sin que se vea el motivo. Instrumenta el error HTTP real (código + cuerpo) en vez de
  capturarlo en silencio.

- **La cola importa más que la media.** Una herramienta puede tener mediana de 16 s y p90 de 106 s,
  con máximos de 286 s. Mide mediana, p90 y máximo, y cuenta cuántas veces devuelve **lista vacía**
  (fiabilidad) — es lo que separa dos herramientas con el mismo acierto medio.

- **La memoria intra-sesión hace que «frío» signifique cosas distintas.** Si el banco se filtra, un
  turno puede aparecer como «frío» solo porque su sesión aporta un único turno a la muestra. Antes
  de sacar conclusiones del estrato frío, comprueba cuántas sesiones aportan un solo turno: esos
  son fríos por construcción, no por ser el primero de la sesión.

## 5. Sesgo del generador de preguntas

Si las preguntas las redacta un modelo, **el generador decide el ganador**. Medido: generadas desde
el **contenido** del fichero, gana la herramienta que lee contenido; generadas desde el **resumen
del índice**, gana la que lee metadatos. No hay formulación neutral.

Práctica: usa las **peticiones originales del usuario** como conjunto principal (es el único
diseño neutro) y deja las sintéticas como batería de sensibilidad cruzada (contenido / resumen del
índice / diff del commit / descripción del PR). Si el orden de sistemas cambia según el generador,
**ese es el hallazgo** y ninguna cifra sintética se usa para decidir.

Y declara siempre de qué se generaron las preguntas en la misma frase que el resultado.

## 6. Guardar la evidencia

Deja en el repositorio del experimento: los turnos extraídos (JSONL con secuencia de `read`/`edit`),
un JSON por sistema medido con el R@5 por caso, los scripts de extracción y de benchmark, y el
README con las fases y los umbrales acordados **antes** de medir. Sin los casos crudos, ninguna
cifra es republicable y la siguiente sesión repite el trabajo.
