#!/usr/bin/env python3
"""Verifica un par PRD + ROADMAP generado como documentos largos.

Chequeos (todos mecánicos, ninguno "a ojo"):
  1. Las fichas de tarea del roadmap y las filas de la tabla de dependencias coinciden
     (sin huérfanas ni duplicadas en ninguno de los dos lados).
  2. El grafo de dependencias es un DAG: detecta ciclos.
  3. Todos los requisitos del PRD tienen cobertura (su id aparece en el roadmap).
  4. Los diagramas mermaid existen y no referencian nodos sin declarar.
  5. Conteo de secciones de ambos documentos (para detectar pisados de fichero:
     un documento que empieza por la sección 6 ha perdido el head).

Uso:
  python3 verify_prd_roadmap.py [PRD.md] [ROADMAP.md]
  python3 verify_prd_roadmap.py --req-prefix F --task-prefix T PRD.md ROADMAP.md

Exit 0 = todo OK. Exit 1 = hay fallos (los imprime con prefijo FALLO).
"""

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path


def read(p):
    path = Path(p)
    if not path.exists():
        sys.exit(f"FALLO: no existe {path}")
    return path.read_text(encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prd", nargs="?", default="PRD.md")
    ap.add_argument("roadmap", nargs="?", default="ROADMAP.md")
    ap.add_argument("--req-prefix", default="F", help="prefijo de los requisitos del PRD (F1, F2...)")
    ap.add_argument("--task-prefix", default="T", help="prefijo de las tareas del roadmap (T1.1...)")
    a = ap.parse_args()

    prd, rm = read(a.prd), read(a.roadmap)
    RQ, TK = re.escape(a.req_prefix), re.escape(a.task_prefix)
    fallos = []

    # 1. fichas de tarea vs tabla de dependencias
    fichas = re.findall(rf"^#{{3,4}} ({TK}[\d.a-z]+)\s*[—:-]", rm, re.M)
    dup = sorted({t for t in fichas if fichas.count(t) > 1})
    if dup:
        fallos.append(f"fichas de tarea duplicadas: {dup}")

    filas = re.findall(rf"^\| ({TK}[\d.a-z]+) .*? \| (.*?) \| (.*?) \|", rm, re.M)
    deps = {f[0]: f[1] for f in filas}
    if len(deps) != len(filas):
        fallos.append("hay ids de tarea repetidos en la tabla de dependencias")

    solo_ficha = sorted(set(fichas) - set(deps))
    solo_tabla = sorted(set(deps) - set(fichas))
    if solo_ficha:
        fallos.append(f"tareas con ficha pero sin fila en la tabla: {solo_ficha}")
    if solo_tabla:
        fallos.append(f"tareas en la tabla pero sin ficha: {solo_tabla}")

    # 2. DAG
    grafo = defaultdict(list)
    for tarea, dep in deps.items():
        for x in re.findall(rf"{TK}[\d.a-z]+", dep):
            if x != tarea:
                grafo[x].append(tarea)
    color, ciclos = defaultdict(int), []

    def dfs(n, camino):
        color[n] = 1
        for m in grafo[n]:
            if color[m] == 1:
                ciclos.append(camino + [n, m])
            elif color[m] == 0:
                dfs(m, camino + [n])
        color[n] = 2

    for n in sorted(set(list(grafo) + list(deps))):
        if color[n] == 0:
            dfs(n, [])
    if ciclos:
        fallos.append(f"ciclos de dependencias: {ciclos}")

    # 3. cobertura de requisitos
    reqs = re.findall(rf"^\*\*({RQ}\d+)\.", prd, re.M)
    sin_cubrir = [r for r in reqs if not re.search(rf"\b{r}\b", rm)]
    if sin_cubrir:
        fallos.append(f"requisitos del PRD sin cobertura en el roadmap: {sin_cubrir}")

    # 4. mermaid
    bloques = re.findall(r"```mermaid(.*?)```", rm, re.S)
    if not bloques:
        fallos.append("el roadmap no tiene ningún bloque mermaid")
    for b in bloques:
        nodos = set(re.findall(r"^\s*([A-Za-z_][\w]*)\[", b, re.M))
        refs = set(re.findall(r"-->\s*([A-Za-z_][\w]*)", b)) | set(
            re.findall(r"^\s*([A-Za-z_][\w]*)\s*-->", b, re.M)
        )
        huerfanos = sorted(refs - nodos)
        if huerfanos:
            fallos.append(f"mermaid referencia nodos no declarados: {huerfanos}")

    # 5. secciones y pisado de fichero
    sec_prd = re.findall(r"^## (.+)$", prd, re.M)
    sec_rm = re.findall(r"^## (.+)$", rm, re.M)

    print(f"PRD     : {a.prd} — {len(prd)} chars, {len(sec_prd)} secciones ##")
    print(f"ROADMAP : {a.roadmap} — {len(rm)} chars, {len(sec_rm)} secciones ##")
    print(f"requisitos detectados : {len(reqs)}")
    print(f"tareas (fichas/tabla) : {len(fichas)}/{len(filas)}")
    print(f"bloques mermaid       : {len(bloques)}")
    print("grafo                 : " + ("con ciclos" if ciclos else "DAG válido"))
    if sec_rm and not sec_rm[0].strip().startswith(("0", "1")):
        print(f"  AVISO: el roadmap empieza por «{sec_rm[0]}» — ¿se ha pisado el head?")
    if sec_prd and not sec_prd[0].strip().startswith("1"):
        print(f"  AVISO: el PRD empieza por «{sec_prd[0]}» — ¿se ha pisado el head?")

    if fallos:
        print()
        for f in fallos:
            print(f"FALLO: {f}")
        return 1
    print("\nOK: paridad de tareas, DAG sin ciclos, cobertura completa y mermaid íntegro.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
