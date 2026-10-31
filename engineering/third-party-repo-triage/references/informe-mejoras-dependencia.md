# Informe de mejoras de una dependencia upstream

Caso: el usuario pasa la URL de un repo (o de una de sus ramas) que ya usa —Bun, Next, una
librería— y pide «revisa las mejoras y hazme un informe». No es auditar el repo para adoptarlo:
es decirle qué cambia para SU stack. Salida: informe HTML cerrado (ver skill
`informe-html-vercel-discord`) con veredicto arriba y las cifras de impacto.

## 1. Fijar primero qué se está informando

Antes de leer nada, resuelve las tres cosas que se confunden entre sí:

| Pregunta | Cómo se contesta |
| --- | --- |
| ¿Existe la rama que me pasaron? | `git ls-remote <url> refs/heads/RAMA refs/heads/main refs/tags/TAG` |
| ¿Qué versión tengo instalada? | `<bin> --version` (no lo que diga el repo) |
| ¿Qué canal es «lo nuevo»? | `curl -sS https://registry.npmjs.org/<pkg> \| python3 -c "import json,sys;print(json.load(sys.stdin)['dist-tags'])"` |

Trampa medida: el enlace a `/tree/canary` de un repo grande respondía 200 pero `canary` era un
tag de 2022; la build «canary» diaria salía de `main`. Escribirlo en el informe evita que el
usuario siga mirando la rama equivocada.

## 2. La lista de cambios: del log de git, no de un changelog

Los repos grandes no mantienen `CHANGELOG.md` (404 en todas las ramas) y la release estable
solo enlaza al blog del vendedor. La fuente fiable:

```bash
D=$(mktemp -d); cd "$D" && git init -q . && git remote add origin https://github.com/OWNER/REPO.git
git fetch -q --depth=600 --filter=blob:none origin main
git log --format='%H%x09%aI%x09%s' FETCH_HEAD > /tmp/log.tsv
```

- `--filter=blob:none` evita descargar el contenido: segundos incluso en repos de 1 GB.
- Filtra por fecha posterior al tag estable que tienes instalado → esa es la lista real de cambios.
- `--depth=N` suficiente para cubrir desde la release estable; comprueba que la fecha más antigua
del log es anterior a esa release, si no sube la profundidad.
- La API de GitHub **miente o se contradice** en este terreno (devolvió el commit inicial de 2022
  para una consulta de commits y `status: behind` con la rama delante en `compare`). No la uses
  como fuente de fechas; úsala solo para PRs concretos.

## 3. De 400 commits a un informe útil

1. **Cuenta y fecha**: `N` commits en `D` días desde tu versión. Es la primera cifra del informe.
2. **Agrupa por prefijo de asunto** (`^scope:`) con un contador en Python y ordena por frecuencia.
   Bun dio: 44 TLS, 23 node:http, 23 Bun.serve, 21 bundler, 20 fetch, 16 React Compiler, 12 sql…
3. **Separa features de arreglos.** Las palabras clave engañan (`release the event loop ref` no es
   una feature, es una fuga de memoria arreglada). El informe se estructura en dos bloques: «lo que
   te cambia el día a día» (features) y «qué se ha arreglado» (por área, con las que tocan
   seguridad o rendimiento destacadas).
4. **Para cada feature candidata, lee el PR entero**: `curl -sS
   https://api.github.com/repos/OWNER/REPO/pulls/<n>` — el cuerpo trae las tablas de benchmark,
   los límites («solo comprueba, no emite») y la fecha de merge. Eso es lo que convierte una línea
   de log en un párrafo honesto.
5. **Cruza con el stack del usuario**: solo entran las áreas que él usa (Next/React, TS, Bun.serve,
   bundler, tests, instalador). El resto, una línea o fuera.
6. **Comprueba en la máquina si la feature está disponible**: ejecutar el binario instalado con el
   subcomando nuevo resuelve la duda en un segundo (`bun check` → `Script not found`). Un informe
   que dice «se mergeó ayer y no está en release» sin haberlo comprobado es medio informe.
7. **Qué NO hacer con canary/builds diarias**: probarlas solo en local, nunca en CI ni en repos que
   despliegan a producción; y decir explícitamente que el gate actual no se cambia hasta que la
   herramienta salga en estable y coincida con la referencia (error a error, en repos reales).

## 4. Etiquetado de las cifras

Las cifras de benchmark son del vendedor hasta que se reproducen. Márcalo en el informe
(`[OFICIAL]` en el PR del propio repo, `[3º]` medición independiente, `[MKT]` marketing, `[NO
reproducidas]` las que no has corrido tú) y deja una sección corta de «cómo se ha verificado»
listando el comando con el que sale cada dato. En el chat, el veredicto en tres o cuatro líneas y
una propuesta concreta de qué medir para decidir la adopción.
