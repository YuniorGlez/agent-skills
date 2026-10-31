# Evaluar un modelo o servicio de fuera con medición real

Se usa cuando llega un lanzamiento (un modelo nuevo, un servicio, un endpoint) y la pregunta es «¿esto nos
mejora?». El entregable no es una opinión: es un informe con cifras propias más una clasificación de adopción.

## 0. Antes de medir nada

```bash
# ¿qué precio y qué contexto tiene DE VERDAD cada proveedor que lo sirve?
curl -s https://openrouter.ai/api/v1/models | python3 -c "import sys,json;[print(m['id'],m['context_length'],m['pricing'],m['architecture']['input_modalities']) for m in json.load(sys.stdin)['data'] if '<filtro>' in m['id']]"
curl -s https://openrouter.ai/api/v1/models/<id>/endpoints      # precio, cuantización, contexto y uptime por proveedor
curl -s -H "Authorization: Bearer $OPENROUTER_API_KEY" https://openrouter.ai/api/v1/credits   # saldo
```

El id suele estar servido por varios proveedores con contextos y precios distintos (262k vs 1M): el número que
citas tiene que ser el del endpoint que sirve la llamada, no el de la página del catálogo. Y si el saldo es bajo, se
dice ANTES de lanzar el lote, no cuando muere a mitad.

## 1. La familia antes que el titular

```bash
curl -s "https://huggingface.co/api/models?author=<org>&search=<familia>&limit=100"   # repos hermanos: GGUF, NVFP4, ASR, rerank...
curl -sL https://huggingface.co/<org>/<repo>/raw/main/README.md | sed -n '1,70p'      # licencia, idiomas, benchmarks declarados
```

La card da en crudo lo que el titular esconde: licencia (`license_name`), idiomas soportados, WER/benchmarks
declarados y «ready for commercial or non-commercial use» cuando lo dice. Con eso se decide qué merece prueba y
qué no se prueba nunca (un 120B no cabe donde un 8B sí). Etiquetar cada cifra del fabricante: [OFICIAL] card/doc ·
[3º] medición independiente · [MKT] marketing · [NV] no verificado.

## 2. Congelar el set ANTES de mirar resultados

Escribir la lista de casos (vídeos, audios, consultas, prompts) a un fichero y guardar su `sha256`. Se decide de
antemano **una métrica por pregunta** (coste, latencia, acierto contra referencia, conformidad de esquema, recall@k)
y se anota el método de etiquetado, incluidas sus debilidades («etiqueta débil: consulta = título del documento»).
Sin set congelado, cada ronda acaba comparando cosas distintas.

## 3. Un eje por subagente, con brief cerrado

Cuatro lotes disjuntos funcionan bien y corren en paralelo: (a) coste/calidad de la capacidad estrella contra el
modelo que ya usamos, (b) precisión contra una referencia independiente, (c) integración real en NUESTRO stack
(recuperación, pipeline de transcripción…), (d) encaje como modelo de agente (tool calling, salida estructurada,
contexto largo) y viabilidad local.

Cada brief debe llevar, literalmente:

- **Directorio compartido de crudos**, con escritura **incremental** (un hijo que muere por timeout no debe llevarse
  la medición).
- **Time-box** en minutos y «entrega parcial obligatoria si te quedas sin tiempo o sin acceso».
- **Prohibición de inventar**: toda cifra debe salir de un fichero escrito; si algo no se pudo medir, `null` + el
  bloqueo literal (comando y error).
- **Prohibido**: tope de tokens de salida, tocar Discord, enviar emails, `git commit/push`; datos de cliente contra
  modelos `:free`.
- **Formato de salida fijo**: JSON con `tests_realizados`, `result_files` (rutas absolutas), `headline_numbers`,
  `blockers`, `recomendacion` en 3-5 líneas.
- Tope de gasto explícito cuando el lote llama a una API de pago.

## 4. El padre verifica; el autorreporte no es prueba

- Extraer el ground truth y mirarlo uno mismo: frames con `ffmpeg -ss T -i clip.mp4 -frames:v 1 out.png` para
  respuestas sobre vídeo, el documento para respuestas sobre recuperación, la traza real para código.
- Comprobar que cada cifra del informe existe en los crudos, y que el total declarado cuadra con el número de casos.
- Un hijo que dice «funciona» tras reportar el arnés caído no ha verificado nada: pide el fichero o repite la llamada.

## 5. Criterio de decisión (dos ejes, nunca uno)

Una métrica sola elige mal: el modelo barato puede ganar en coste y perder en lo que no se mide (diarización de
hablantes, licencia, manejo de datos de cliente, techo de calidad). Cada veredicto va con su número, con lo que el
número no ve, y clasificado en **hacerlo ya / ya lo tienes / aparcado con disparador / no hacerlo** — cada «no» con
qué lo cambiaría.

## 6. Qué NO se mide así

Post-entrenar o adaptar pesos no se prueba «un poco»: coste de GPU alto y resultado a semanas. Se deja como
«aparcado con disparador» (con el disparador escrito) salvo que el cliente lo pida y lo pague.
