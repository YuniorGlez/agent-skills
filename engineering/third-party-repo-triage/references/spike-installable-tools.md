# Spike de herramientas instalables (fase 2 del triage) — validado 8-ago-2026

Cuando el operador aprueba un candidato del triage, el siguiente paso es un SPIKE:
instalar, probar con datos reales, medir y emitir veredicto. Casos reales de la
misma jornada: tokenjam (veredicto: útil pero sin integración con el stack),
agentready (veredicto: adoptado como servicio), vpskill (skill adoptado).

## Secuencia que funciona

1. **Instalar con uv tool** (nunca pip global; el Mac de el operador tiene uv 0.12+,
   binarios en ~/.local/bin):
   ```bash
   uv tool install <name>   # → <name> --version para confirmar
   ```
2. **Leer el README del repo clonado** en research-30d-repos/ (o docs/) ANTES de
   correr nada: identifica el modo de uso real, los flags no interactivos y
   qué fuentes de datos admite (backfill, live, archivos).
3. **Probar con datos reales de la máquina**, no con demos del repo. Buscar
   primero qué telemetría/sesiones existen: `~/.codex/`, `~/.claude/projects/`,
   `~/.local/share/opencode/opencode.db`, configs globales (~/.config/<tool>/).
4. **Verificar la integración real antes de prometer valor**: si la herramienta
   depende de telemetría OTel de tus coding agents, comprobar que los emiten:
   `grep -rl "otlp\|opentelemetry" <dir>/dist/` — si no hay matches, el backfill
   no cubrirá tu stack (caso tokenjam vs opencode: opencode NO emite OTel →
   tokenjam solo sirve para Claude Code/Codex/SDK propios).
5. **Medir y guardar evidencia**: reportes JSON/MD del propio tool +
   `wc -w`/tokens antes-después de cualquier fix. README de cierre en
   `~/projects/<mi-spike>/` con: instalación, evidencia real,
   limitaciones, veredicto en 1 frase, artefactos.
6. **Veredicto en lenguaje llano** (el operador): adoptar / adoptar con matices /
   no aplica al stack actual. Incluir SIEMPRE la limitación de alcance.

## Variante: la herramienta engancha hooks en OTROS agentes (no solo su binario)

Cuando el candidato no es una CLI sino un hook que instala entradas en Claude Code, Codex, OpenCode o Pi,
el spike cambia de forma: el riesgo ya no es que la herramienta no valga, es que te toque los configs de los
agentes que el usuario usa a diario. Receta que funcionó:

1. **Aisla su propio estado antes de nada.** Estas herramientas escriben en el HOME del usuario. Redirige su
   directorio de estado (`ABIDE_HOME_DIR`, `XDG_*`, `--config-dir`…) **y** `HOME` a un sandbox, o el `init`
   global te deja hooks en `~/.claude/settings.json` y `~/.codex/hooks.json` del usuario real.
2. **Instala en modo `--project`** (escribe dentro del repo) y, aun así, **fotografía con sha256 los configs
   reales antes y después** (`shasum -a 256 ~/.claude/settings.json ~/.codex/hooks.json`) para poder afirmar
   «no te toqué nada» con hash, no con fe.
3. **Clona el repo objetivo con `git clone --local`** para tener historial real (con el que probar la fase
   «turn» y la calibración) sin gastar ancho de banda ni tocar el original.
4. **Prueba primero el contrato de robustez**, que es lo que la herramienta promete: stdin vacío, JSON roto,
   evento desconocido, sin clave, `cwd` inexistente, payload enorme, subcomando inventado. Un hook bien hecho
   sale **exit 0** en todos. Es barato (segundos) y decide si merece la pena seguir.
5. **Mide la precisión con un parche etiquetado a mano, no con su benchmark.** Escribe a mano un cambio que
   viola cada regla y su gemelo limpio, guarda los dos como `.patch` y pásalos con el modo no interactivo
   (`check --diff X --json`). Repite 3 veces por caso: estos modelos no son deterministas y la dispersión de
   una misma llamada es parte del dato.
6. **Lee el log de uso de la propia herramienta** para el coste real de una tarea (tokens, latencia, si llegó
   a bloquear), en vez de estimarlo. Suele escribir un JSONL por repo.
7. **El coste de la fase de compilación lo paga el agente, no la herramienta**: cuenta los tokens que gastó
   el que compiló (lo imprime `codex exec` al final) y dilo en el veredicto.

**Pitfall que cuesta una conclusión falsa:** si el agente que compila se queda sin acceso a ficheros que el
skill le pide (el arnés de permisos le corta un directorio fuera del repo, se ve en el log como
`permission requested: external_directory … auto-rejected`), **no se detiene**: mete lo que sí alcanza en un
solo cajón y declara éxito. Síntoma medible: todas las reglas en el mismo bucket y un reparto imposible para
la herramienta. Comprueba el reparto por cajones y, si sale plano, repite la compilación con la orden acotada
al repositorio antes de escribir el veredicto.

## Pitfalls de la sesión

- **`bun add` bloquea los `postinstall` por defecto y eso rompe paquetes con binarios nativos.**
  El CLI muere con `No native build was found for platform=darwin arch=arm64` al cargar el
  primer grammar o binding que no tiene `prebuilds/`. No es un fallo de la herramienta ni de la
  plataforma: es el escudo de bun, que es correcto y hay que respetar. Diagnóstico y arreglo:
  ```bash
  bun pm untrusted          # lista qué postinstall quedaron bloqueados
  bun pm trust --all        # autoriza los del proyecto y los ejecuta
  ```
  Si el paquete no trae `prebuilds/` para la plataforma (comprueba con
  `ls node_modules/<paquete>/prebuilds/`), hay que compilarlo a mano en su carpeta:
  `npx --yes node-gyp rebuild` (requiere Xcode Command Line Tools; tarda minutos). Un único
  grammar sin prebuild que se cargue al inicio tumba el CLI entero, así que vale la pena
  arreglarlo antes de descartar la herramienta.
- **Wizards interactivos**: `tj onboard --claude-code` pregunta el plan de pago
  etc. El pty NO entrega la respuesta de forma fiable; usar pipe:
  `printf '1\n0\n0\nn\n' | tj onboard --claude-code` (respuestas en orden de
  las preguntas). Mejor aún: buscar flags pre-answered (`--claude-code`,
  `--codex`) que saltan parte del wizard.
- **Onboard puede instalar LaunchAgents**: tokenjam dejó `com.tokenjam.serve`
  (daemon del dashboard Lens :7391). Verificar con `launchctl list | grep -i
  tj` y reportarlo — es el "daemon persistente" que el triage ya había anotado.
- **Falsos negativos de detectores**: agentready marcó `lock_files: FAIL` en un
  repo con bun.lock (116KB) — solo mira package-lock/yarn/pnpm. Leer la
  evidencia del reporte antes de "arreglar" algo que ya existe; documentar el
  gap del detector en el veredicto.
- **Proyección de remediación desde el JSON del reporte**: agentready emite
  `assessment-*.json` con findings[{attribute{tier,default_weight}, score,
  status}]. Fórmula: score = Σ(score×weight) / Σ(weights de evaluados).
  Proyectar por tiers (T1→T2→T3/4) da el plan de mejora con números exactos:
  base la agencia 46.1 → +T1 (6 fixes) 77 → +T2 (12) 94 → todos (16) 100.
- **Skills de terceros**: SkillGate scan (SkillSpector --no-llm) antes de copiar
  a ~/.hermes/skills/. Falsos positivos esperados en skills de solo-markdown:
  P6 "prompt extraction" (el skill enseña prompts, es su función) y YARA
  info_stealer en ejemplos de texto (verificar la línea antes de alarmarse).
- **No configurar herramientas del ecosistema muerto**: el operador ya no usa
  Claude Code (8-ago-2026) → los fixes que tokenjam proponía para
  ~/.claude/ (hooks, skills, settings) NO se aplican; transferir la lección al
  stack vivo (opencode AGENTS.md, config de Hermes).

## Ejemplo de fix real transferido (tokenjam → stack vivo)
La lección del analyzer `summarize` (instrucciones infladas) aplicada al fichero
que SÍ se carga en cada sesión de opencode: ~/.config/opencode/AGENTS.md
1.528→1.367 palabras (-10.5%, ~-217 tok/sesión) eliminando secciones muertas de
LiteLLM/Langfuse (verificado: sin proceso, sin HTTP, docker vacío; backup
`.tokenjam-backup-YYYYMMDD`; respetar bloques marcados <!-- tool:... -->).
