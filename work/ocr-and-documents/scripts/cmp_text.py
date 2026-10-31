#!/usr/bin/env python3
"""Compara la salida de un parser documental candidato contra el ground truth de un PDF digital.

Uso:
  python3 cmp_text.py --cand out/doc.md --pdf doc.pdf
  python3 cmp_text.py --cand out/doc.md --gt gt.txt

Salida: recall/precisión multiset de palabras (normalizadas), tokens ausentes y señales de
dominio (signos de apertura en español, imágenes remotas referenciadas). El ground truth por
defecto es `pdftotext -layout`, que solo vale para PDFs digitales; para escaneados compara
contra una transcripción humana.
"""
import argparse
import re
import subprocess
import sys
import unicodedata
from collections import Counter


def normalize(text: str) -> list[str]:
    text = re.sub(r"!\[\]\([^)]*\)", "", text)      # enlaces de imagen del vendor
    text = re.sub(r"[#*_|>`~-]", " ", text)         # marcado Markdown
    text = unicodedata.normalize("NFC", text).lower()
    return re.findall(r"[0-9a-záéíóúñüçàèìòùâêîôû]+", text)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cand", required=True, help="Markdown/JSON del parser candidato")
    ap.add_argument("--pdf", help="PDF digital de origen (usa pdftotext -layout)")
    ap.add_argument("--gt", help="ground truth ya extraído a texto")
    ap.add_argument("--top", type=int, default=25, help="cuántos tokens perdidos listar")
    args = ap.parse_args()

    cand = open(args.cand, encoding="utf-8", errors="replace").read()
    if args.gt:
        gt = open(args.gt, encoding="utf-8", errors="replace").read()
    elif args.pdf:
        proc = subprocess.run(["pdftotext", "-layout", args.pdf, "-"], capture_output=True)
        if proc.returncode != 0:
            print("pdftotext falló; ¿es un PDF escaneado? usa --gt", file=sys.stderr)
            return 2
        gt = proc.stdout.decode("utf-8", "replace")
    else:
        ap.error("hace falta --pdf o --gt")

    a, b = normalize(cand), normalize(gt)
    if not b:
        print("ground truth vacío: el PDF no tiene capa de texto", file=sys.stderr)
        return 2
    ca, cb = Counter(a), Counter(b)
    common = sum((ca & cb).values())
    print(f"palabras candidato: {len(a)} | ground truth: {len(b)}")
    print(f"recall   : {common / len(b):.4f}")
    print(f"precisión: {common / max(len(a), 1):.4f}")

    missing = cb - ca
    print(f"\ntokens del ground truth ausentes: {sum(missing.values())} "
          "(cabeceras/pies filtrados por diseño cuentan aquí)")
    print(missing.most_common(args.top))

    print("\nseñales de dominio:")
    for mark in ("¿", "¡"):
        print(f"  {mark}: candidato={cand.count(mark)} ground_truth={gt.count(mark)}")
    print(f"  imágenes remotas referenciadas: {len(re.findall(r'!\\[\\]\\(', cand))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
