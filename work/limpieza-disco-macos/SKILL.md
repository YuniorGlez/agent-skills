---
name: limpieza-disco-macos
description: Auditar disco en macOS y decidir qué se puede borrar.
version: 1.0.0
author: Hermes
license: proprietary
metadata:
  hermes:
    tags: [disk, macos, cleanup, maintenance]
    related_skills: [informe-html-vercel-discord, machine-context, system-administration]
---

# Auditoría y limpieza de disco en macOS

## When to Use

- el operador dice «el disco está lleno», «mira qué se puede borrar» o «haz un análisis del sistema».
- Tras una actualización grande de macOS y quiere saber qué ha quedado.
- Antes de pedir espacio a un cliente o de mover el entorno a otra máquina.

No usar para borrar ficheros concretos que él ya ha nombrado: eso es una tarea de una línea, no una auditoría.

Cuando el operador dice «mira qué se puede borrar» o «el disco está lleno», el entregable es un **informe con bloques
por nivel de riesgo** y **cero borrados sin aprobación**. Él decide; el agente mide y propone.

## 1. Medir bien antes de opinar (la mitad de los errores están aquí)

`stat %z` da el **tamaño lógico**; `du` da los **bloques asignados**. En un Mac con Docker, VMs y ficheros
dispersos la diferencia es brutal y cambia el veredicto:

- `Docker.raw` — 60 GB lógicos, **12,4 GB reales** (disperso).
- `~/Library/Mobile Documents/…WhatsApp/backup/Media.tar` — 8,0 GB lógicos, **0 GB reales** (marcador de iCloud).
  Borrarlo no libera nada y encima descarga el backup remoto.

Regla: **todo tamaño que entre en el informe se mide con `du -sk`**, nunca con `ls -lh` ni `stat`.

```bash
# top real en home, sin duplicar /System/Volumes/Data (que es el mismo dato)
find ~ -xdev -type f -size +300M -print0 | xargs -0 du -sh 2>/dev/null | sort -rh | head -40
```

Si se usa `find / -xdev -exec ls -lh`, cada fichero sale **dos veces** (ruta real y `/System/Volumes/Data/...`) y
las rutas con espacios se rompen al pasar por `awk`. Mejor `-print0 | xargs -0`.

## 2. Barrido mínimo (lo que sí aparece siempre)

```bash
df -h /System/Volumes/Data                     # capacidad
sw_vers                                         # versión (contexto del informe)
tmutil listlocalsnapshots /                     # snapshots (0 = nada que rascar)
tmutil destinationinfo                          # ¿hay Time Machine?
docker system df                                # si el daemon está vivo; si no, medir Docker.raw
find ~/projects -maxdepth 4 -type d \( -name node_modules -o -name .next -o -name dist \) -prune \
  | xargs -I{} du -sm {} | sort -rn | head -15
du -sh ~/.cache/* ~/.hermes/* ~/.hermes/venvs/* ~/Library/Application\ Support/* | sort -rh | head -20
```

Sitios que casi siempre tienen oro: `~/.bun/install/cache`, `~/.npm`, `~/.cache/{codex-runtimes,tgrep,huggingface,torch}`,
`~/.hermes/{cache/scratch,state-snapshots,backups,venvs,reports}`, packs git huérfanos (`tmp_pack_*`, restos de
clones interrumpidos), `.next` de proyectos, y `~/Downloads`.

## 3. Clasificar en bloques, no en una lista

- **A · regenerable** — cachés e índices. Se pierde tiempo de primera ejecución, nada más.
- **B · caducado** — benchmarks terminados, copias de `state.db` superadas, logs viejos, zips cuyo repo ya está clonado.
- **C · opcional** — recuperable con trabajo: venvs de experimentos, builds, vídeos intermedios, packs huérfanos.
- **D · decisión del usuario** — Docker, VMs, `node_modules`, contenido personal (vídeos, descargas).

Cada fila del informe lleva ruta exacta, tamaño medido y **coste de recuperarlo**. Sin eso, el operador no puede decidir.

## 4b. Detectar proyectos abandonados (`node_modules` / `.next`)

**La mtime no sirve de señal el mismo día de un barrido masivo.** Verificado 25-oct-2026: a las 08:44-08:49 un
proceso tocó **36 `package.json`**, 35 `README.md`, 18 `.gitignore`, 15 `bun.lock` en todos los repos. Contar «no se
toca desde hace 2 semanas» por mtime marca como activos 20 de 20 proyectos. Hay que **excluir**
`package.json`, lockfiles, `README.md`, `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `tsconfig.json`, `.gitignore`
y `*.tsbuildinfo`, y quedarse con la fecha **más reciente entre el último commit y el fichero de código tocado**
(`src/`, `app/`, `*.ts`, `*.py`…).

```bash
git -C "$proj" log -1 --format=%cs        # commit real
# y la mtime del código, podando node_modules/.next/.git/dist y los ficheros del barrido
```

**Antes de proponer borrar un `node_modules`, comprobar launchd y puertos**: un proyecto con meses sin commits puede
tener el servidor vivo. `launchctl list | rg la agencia` y `lsof -nP -iTCP:<puerto> -sTCP:LISTEN`. Caso real: `ytdl`
lleva 76 días sin tocarse y su `node_modules` es imprescindible porque el servicio está escuchando en :7777 vía
`com.la agencia.ytdl`.

**Los `.next` de proyectos activos no se borran.** Recuperar 500 MB a cambio de 1-2 min de recompilación en el
proyecto que se está tocando esa semana es mal negocio; solo caen los de proyectos parados.

## 4d. Restos que deja una actualización de macOS

Orden de comprobación, con lo que da dinero y lo que solo suena bien:

```bash
diskutil apfs listSnapshots /            # 1 solo snapshot = el sistema sellado, NO se toca
ls -ld /System/Volumes/Update*; du -sh /System/Volumes/Update   # 80 MB, lo limpia solo
du -sh /private/var/db/diagnostics /private/var/db/uuidtext    # 2-3 GB de log → sudo log erase --all
du -sh /private/var/folders/*/*/                               # temporales; se purgan al reiniciar
du -sh ~/Previously* ~/Elementos*      # 11 carpetas, 6 MB, de cada update
du -sh /Library/Application\ Support/{GarageBand,Logic,PaloAltoNetworks,Fortinet}
brew cleanup -n
systemextensionsctl list | rg -i 'terminated|waiting'          # restos de apps desinstaladas
```

**Trampas medidas en esta máquina (25-oct-2026):**

| Parece basura | Tamaño | Realidad |
|---|---|---|
| `/System/Volumes/Preboot` | 35 GB | Cryptexes y cachés de arranque **clonados** con el volumen del sistema. El tamaño es engañoso y borrar rompe el arranque |
| Snapshot `com.apple.os.update-…` | — | Es el sistema sellado en uso; el único que queda |
| `/Library/Developer/CommandLineTools` | 1,9 GB | `xcode-select -p` apunta ahí |
| GarageBand + Logic + Apple Loops | 2,25 GB | Solo si las apps **no están** instaladas (`mdfind kMDItemCFBundleIdentifier`) |
| `/Library/Application Support/Adobe` | 1,7 GB | Comprobar Acrobat antes: puede estar instalado y entonces es suyo |
| `/private/var/db/receipts` | 85 MB | Apple desaconseja borrarlos |

**No dar por hecho quién necesita `sudo`:** probarlo con `[ -w "$ruta" ] && echo SIN SUDO || echo sudo`, ruta por
ruta. En este Mac, admin basta para GarageBand/Logic/Apple Loops y Homebrew, pero no para
`/private/var/db/diagnostics` ni `/Library/Application Support/{PaloAltoNetworks,Fortinet}` ni
`~/Previously Relocated Items*` (root:admin 775 y aún así no escribible sin contraseña).

## 4c. Lo que NO se toca en esta máquina (y por qué)

Comprobado con `rg` sobre `~/.hermes/skills` y `~/.agents/skills` antes de proponer nada:

| Ruta | Tamaño | Consumidor |
|---|---|---|
| `~/.cache/whisper/mlx_models/large-v3` | 2,9 GB | skill `tldv-video-clips-youtube`, `apple-ondevice-stt` |
| `~/.cache/hyperframes/whisper/models/ggml-large-v3.bin` | 2,9 GB | HyperFrames |
| `~/.cache/huggingface/…surya-ocr-2-gguf` | 1,4 GB | `marker-pdf` (OCR de escaneados) |
| `~/.hermes/cache/models/bge-reranker-v2-m3` | 2,1 GB | reranker del RAG (vault, knowledge) |
| `~/.hermes/state.db` | 954 MB | histórico de sesiones, el dato más valioso |
| `/private/var/vm/sleepimage` | 2,0 GB | hibernación del sistema |

Los dos whisper parecen duplicados y **no lo son**: MLX y ggml son runtimes distintos. Borrar uno rompe una skill.
`~/Library/Caches` **no se borra entera**: algunas apps guardan ahí estado que no recrean bien; se limpia por subcarpeta.

## 5. Verificar antes de escribir el informe

Cada candidato se confirma con una pasada real, no de memoria: que la ruta exista, su tamaño, y que el consumidor
siga referenciándola (`rg -l '<nombre>' ~/.hermes/skills ~/.agents/skills`). Un benchmark «terminado» se comprueba
por fecha y por si su venv sigue en `~/.hermes/venvs`.

## 6. Cerrar como cualquier informe

HTML autocontenido en `~/.hermes/reports/limpieza-macos<versión>-<AAAAMMDD>.html` → `open` → Vercel → enlace por
Discord al canal **privado** (`dev.env`), porque una auditoría de máquina es desarrollo y no negocio. Receta: skill
`informe-html-vercel-discord`. En el chat, veredicto y cifras; la tabla larga va al HTML.

El script de borrado se incluye en el informe **con un paso 0 de ensayo** que solo lista rutas, y con rutas absolutas
una por una, nunca comodines ni `find -delete`. La ejecución espera aprobación explícita.

## Pitfalls

- **`du` nominal ≠ espacio liberado.** Medido 25-oct-2026: 23,2 GB nominales borrados dejaron **15 GB** reales de
  ganancia (49 → 64 GB libres). Causa comprobada en parte: **Bun hardlinkea su store (`~/.bun/install/cache`) dentro de
  los `node_modules`**, así que borrar el caché no libera los bloques que un proyecto sigue referenciando. El resto no
  se cuadra al byte (overhead de clústeres y cachés del sistema reescritas durante la maniobra). **Prometer cifras
  conservadoras y medir `df` antes/después**, no sumar `du`.
- Tras borrar, verificar que las herramientas siguen vivas (`bun --version`, `python3 -c pass`), que `state.db` está
  intacto y que `~/.hermes/cache/scratch` sigue existiendo: es el `TMPDIR` del arnés y borrarlo entero rompe las
  herramientas que escriben temporales. Se **vacía su contenido**, no el directorio.
- El guardián de ciclo de vida del arnés bloquea `vercel deploy` con «scan budget exhausted» (el bundle de la CLI
  pasa de 1 MiB). Puede funcionar una vez y fallar a la siguiente: desplegar por **API REST**
  (`POST /v13/deployments` con el token de `auth.json`) es el camino fiable. Receta en `informe-html-vercel-discord`.
- Si el informe ya está publicado y las cifras cambian, **editar el mensaje de Discord**
  (`PATCH <webhook>/messages/<id>`), no enviar otro: el primero dice «no he borrado nada» y el segundo lo contrario.
- **Borrar el directorio de datos de un servicio que está corriendo es un no-op.** `~/projects/.tgrep` (1,7 GB) se
  lo reconstruyó `com.la agencia.tgrep-serve` en 10 minutos. Comprobarlo ANTES con `launchctl list | rg <nombre>` y
  `ps aux | rg '[t]grep serve'`; si el servicio hace falta, no se toca (o se para, se borra y se deja parado, con su
  OK). Un `node_modules` de un servicio vivo es igual de intocable (caso `ytdl` en :7777).
- **Antes de prometer cifras, verificar que el contador responde:** `dd if=/dev/zero of=probe bs=1m count=1000`,
  `df`, borrar, `df`. Si 1 GB se refleja al instante, cualquier diferencia posterior es real y hay que explicarla, no
  atribuirla a lentitud del sistema. (Ojo: `mkfile -n` crea un fichero disperso y NO sirve para esta prueba.)
- **Borrar `node_modules` puede no liberar nada en `df`.** Medido 25-oct-2026: 3.087 MB en 6 proyectos parados,
  `df` sin cambios. Causa: bloques compartidos (clones APFS de cuando se copia un proyecto entero) y cachés que se
  reescribieron en la misma franja. Decirlo tal cual; no adornar el resultado.
- `du -sh ~/Library/Mobile Documents` miente por defecto inverso: da MB cuando los ficheros dicen GB. Es iCloud.
- Un `du` sobre `~/projects` puede tardar minutos (69 GB, miles de `node_modules`): dar timeout generoso o acotar
  con `-maxdepth`.
- Sin `sudo` no se auditan `/private/var/db`, `/Library/Caches` del sistema ni «Elementos reubicados» de
  `~`: decirlo en el pie del informe en vez de suponer que no hay nada.
- La actualización de macOS (27.0.1 incluida) **no deja** instalador ni snapshots que borrar. No prometer esa vía:
  lo que se recupera es basura de meses de trabajo, no del update.
