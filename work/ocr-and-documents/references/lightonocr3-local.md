# LightOnOCR-3 en local (Mac Apple Silicon), medido el 9-oct-2026

- Funciona: pesos oficiales `lightonai/LightOnOCR-3-0.8B` -> `mlx_vlm convert --hf-path <dir> --mlx-path <dir> --dtype bfloat16` -> `mlx_vlm.stream_generate`. Venv `~/.venvs/mlxvlm`. Script de referencia: `./run_mlx.py` (puede haberse podado).
- Ritmo: ~20 tokens/s en M4, de media ~66 s por página; una tabla densa de 4.500 tokens tarda unos 200 s. Prompt vacío = texto plano; prompt `grounding` = cajas + descripciones.
- NO usar Transformers sobre MPS: Qwen3.5 cae a los kernels de referencia (causal_conv1d / gated delta) y una sola página pasa de 5 min.
- Descarga: el backend Xet de HF se cuelga y deja un symlink roto en model.safetensors -> `HF_HUB_DISABLE_XET=1 hf download ... --local-dir`.
- El modo grounding sobre planos o dibujo técnico puede entrar en bucle (filas de "gráfica" repetidas). Poner una guarda de RELOJ por página, nunca un tope de tokens.
- Calidad frente a marker --force_ocr: texto y tablas 0,988 vs 0,885 de recall de palabras (medido contra la capa nativa). En planos marker lee mejor la leyenda y LightOn inventa texto.
- Antes de lanzar OCR, muestrea `get_text_range()` con pypdfium2: los PDF exportados de proyectos técnicos suelen tener texto nativo en más del 99 % de las páginas.
