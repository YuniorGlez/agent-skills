#!/usr/bin/env python3
"""Lee un .xlsx sin dependencias externas (solo stdlib) y vuelca las hojas a texto.
Uso:  python3 xlsx_read.py fichero.xlsx [FiltroDeHoja]
Tambien importable:  sheets(z) / shared_strings(z) / read_sheet(z, target, ss)
"""
import zipfile, re, sys
from xml.etree import ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}

def shared_strings(z):
    out = []
    if "xl/sharedStrings.xml" not in z.namelist():
        return out
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    for si in root.findall("m:si", NS):
        out.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
    return out

def sheets(z):
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rmap = {r.get("Id"): r.get("Target") for r in rels}
    out = []
    for sh in wb.find("m:sheets", NS):
        rid = sh.get("{%s}id" % NS["r"])
        tgt = (rmap.get(rid) or "").lstrip("/")   # openpyxl escribe la barra inicial
        if not tgt.startswith("xl/"):
            tgt = "xl/" + tgt
        out.append((sh.get("name"), sh.get("sheetId"), tgt))
    return out

def col_idx(ref):
    m = re.match(r"([A-Z]+)", ref or "A")
    n = 0
    for c in (m.group(1) if m else "A"):
        n = n * 26 + (ord(c) - 64)
    return n - 1

def read_sheet(z, target, ss, max_rows=None):
    root = ET.fromstring(z.read(target))
    rows = []
    for row in root.iter("{%s}row" % NS["m"]):
        cells = {}
        for c in row.findall("m:c", NS):
            t, v, isel = c.get("t"), c.find("m:v", NS), c.find("m:is", NS)
            if t == "s" and v is not None:
                val = ss[int(v.text)] if v.text and int(v.text) < len(ss) else ""
            elif t == "inlineStr" and isel is not None:
                val = "".join(x.text or "" for x in isel.iter("{%s}t" % NS["m"]))
            else:
                val = v.text if v is not None else ""
            cells[col_idx(c.get("r", ""))] = (val or "").strip()
        if cells:
            rows.append([cells.get(i, "") for i in range(max(cells) + 1)])
            if max_rows and len(rows) >= max_rows:
                break
    return rows

if __name__ == "__main__":
    path = sys.argv[1]
    want = sys.argv[2] if len(sys.argv) > 2 else None
    z = zipfile.ZipFile(path)
    ss = shared_strings(z)
    for name, sid, tgt in sheets(z):
        if want and want.lower() not in name.lower():
            continue
        rows = read_sheet(z, tgt, ss)
        print("\n" + "=" * 100)
        print("HOJA: %s   (sheetId=%s)  filas=%d" % (name, sid, len(rows)))
        print("=" * 100)
        for i, r in enumerate(rows[:400]):
            line = " | ".join(r).rstrip(" |")
            if line:
                print("%3d: %s" % (i + 1, line[:400]))
