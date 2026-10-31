#!/usr/bin/env python3
"""Verifica un fichero "limpio" contra su raw en formato `Nombre [MM:SS]: texto` (tl;dv).

Uso:
    python3 verify_turns.py <raw.md> [<clean.md>]
    (si solo se pasa el raw, deriva clean/<base>_clean.md)

Comprueba:
  1. Nº de turnos por hablante (raw vs clean) — turnos de MÁS = error;
     turnos de menos = normal (muletillas eliminadas, fragmentos fusionados).
  2. Timestamps del raw ausentes en el clean — aviso, revisar si son merges
     intencionados de fragmentos de continuación.
  3. Orden cronológico de los timestamps del clean.
  4. Coincidencia del último timestamp del clean con el del raw.
  5. Contenido duplicado entre turnos (mismo hablante + mismo texto largo en
     timestamps distintos) — típico error al fusionar fragmentos.

Exit 0 = OK (puede haber avisos de revisión manual), 1 = errores, 2 = uso incorrecto.
"""
import re
import sys
from collections import Counter

TURN = re.compile(r'^(.+?)\s*\[(\d{2}:\d{2})\]:', re.M)
MIN_DUP_LEN = 40  # solo avisar de duplicados con texto sustantivo (ignora "Vale." etc.)


def parse(path):
    text = open(path, encoding='utf-8').read()
    turns = []
    for m in TURN.finditer(text):
        spk = m.group(1).strip()
        ts = m.group(2)
        body = text[m.end():].split('\n', 1)[0].strip()
        turns.append((spk, ts, body))
    return turns


def to_min(ts):
    m, s = ts.split(':')
    return int(m) * 60 + int(s)


def main():
    if len(sys.argv) >= 3:
        raw_path, clean_path = sys.argv[1], sys.argv[2]
    elif len(sys.argv) == 2:
        raw_path = sys.argv[1]
        base = raw_path.rsplit('/', 1)[-1]
        clean_path = 'clean/' + base[:-3] + '_clean.md'
        print(f'Derivado clean: {clean_path}')
    else:
        print(__doc__)
        return 2

    raw = parse(raw_path)
    clean = parse(clean_path)
    errors, infos = [], []

    # 1. turnos por hablante
    rc, cc = Counter(t[0] for t in raw), Counter(t[0] for t in clean)
    print(f'RAW turns: {len(raw)} | CLEAN turns: {len(clean)}')
    for spk in sorted(set(rc) | set(cc)):
        delta = cc[spk] - rc[spk]
        flag = '' if delta == 0 else ('  (fusión/filtro ok)' if delta < 0 else '  << MÁS turnos que raw')
        print(f'  {spk}: raw={rc[spk]} clean={cc[spk]}{flag}')
        if delta > 0:
            errors.append(f'{spk} tiene {delta} turnos MÁS que el raw — revisar')

    # 2. timestamps del raw ausentes en el clean
    clean_ts = {t[1] for t in clean}
    missing = [(s, ts) for s, ts, _ in raw if ts not in clean_ts]
    if missing:
        print(f'Timestamps del raw ausentes en clean ({len(missing)}): {missing}')
        infos.append('timestamps ausentes: revisar que sean merges intencionados de fragmentos de continuación')
    else:
        print('Timestamps del raw: todos presentes en clean OK')

    # 3. orden cronológico
    seq = [to_min(t[1]) for t in clean]
    ok = seq == sorted(seq)
    print('Orden cronológico del clean:', 'OK' if ok else 'DESORDENADO')
    if not ok:
        errors.append('timestamps del clean desordenados')

    # 4. último timestamp
    rl, cl = raw[-1][1], clean[-1][1]
    print(f'Último timestamp: raw={rl} clean={cl}', 'OK' if rl == cl else 'NO COINCIDE')
    if rl != cl:
        errors.append('el último timestamp del clean no coincide con el del raw')

    # 5. contenido duplicado entre turnos
    seen = {}
    for spk, ts, body in clean:
        if len(body) >= MIN_DUP_LEN:
            key = (spk, body)
            if key in seen:
                print(f'Contenido duplicado: {spk} [{seen[key]}] y [{ts}]: "{body[:80]}..."')
                infos.append('contenido duplicado: revisar si es repetición real o error de merge')
            else:
                seen[key] = ts

    print()
    if errors:
        print('ERRORES:')
        for e in errors:
            print('  -', e)
        return 1
    print('Verificación completada. Revisión manual pendiente:')
    for i in infos:
        print('  -', i)
    return 0


if __name__ == '__main__':
    sys.exit(main())
