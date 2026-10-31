#!/usr/bin/env python3
"""Comprueba el multi idioma de una web en un navegador de verdad.

Qué mide (y por qué así):
 1. Que el selector cambie `<html lang>` y el título de la pestaña.
 2. Que la elección sobreviva a una recarga, también en el título (el `<title>` de `metadata` de Next
    rehidrata DESPUÉS de los efectos y devuelve el título del servidor si no se ha quitado de ahí).
 3. Que no quede texto de la interfaz anterior: se busca una lista de cadenas que solo existen en el
    idioma de origen. Si aparece alguna, es un texto sin traducir.
 4. Consola sin errores ni avisos (ahí aparece el desajuste de hidratación).

La comparación de DATOS entre idiomas no se puede hacer genérica: búscate un cliente conocido y
compara la fila a mano, o añade aquí el paso con tu selector.

Uso:
  python verificar-idioma.py --url http://localhost:3103 --idiomas es,en,de
  python verificar-idioma.py --url ... --restos-es "Buscar,Vencido,Enviar" --selector "select"
"""

import argparse
import json
import sys

from playwright.sync_api import sync_playwright

# Cadenas que solo existen en la interfaz de origen. Ajustar al proyecto.
RESTOS_POR_DEFECTO = [
    "Buscar", "Todos los estados", "Código", "Vencido", "Responsable", "Sin consulta",
    "Pendiente de cobro", "Claro", "Oscuro", "Enviar", "Escuchando",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--idiomas", default="es,en,de")
    ap.add_argument("--idioma-base", default="es")
    ap.add_argument("--selector", default="select")
    ap.add_argument("--restos-es", default=",".join(RESTOS_POR_DEFECTO))
    args = ap.parse_args()

    idiomas = [i.strip() for i in args.idiomas.split(",") if i.strip()]
    restos = [w.strip() for w in args.restos_es.split(",") if w.strip()]
    otros = [i for i in idiomas if i != args.idioma_base]

    fallos: list[str] = []
    salida: dict = {}

    with sync_playwright() as p:
        navegador = p.chromium.launch()
        pagina = navegador.new_page()
        consola: list[str] = []
        pagina.on(
            "console",
            lambda m: consola.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None,
        )
        pagina.on("pageerror", lambda e: consola.append(f"pageerror: {e}"))

        pagina.goto(args.url, wait_until="networkidle")
        salida["lang_inicial"] = pagina.evaluate("document.documentElement.lang")
        salida["titulo_inicial"] = pagina.title()

        for idioma in otros:
            pagina.select_option(args.selector, idioma)
            pagina.wait_for_timeout(350)
            texto = pagina.inner_text("body")
            lang = pagina.evaluate("document.documentElement.lang")
            titulo = pagina.title()
            quedan = [w for w in restos if w in texto]
            salida[idioma] = {"lang": lang, "titulo": titulo, "restos": quedan}
            if lang != idioma:
                fallos.append(f"{idioma}: <html lang> es {lang!r}")
            if quedan:
                fallos.append(f"{idioma}: quedan textos sin traducir: {quedan}")

            # La recarga: lo que se guarda tiene que aguantar, también el título.
            pagina.reload(wait_until="networkidle")
            lang_recarga = pagina.evaluate("document.documentElement.lang")
            titulo_recarga = pagina.title()
            salida[idioma]["tras_recarga"] = {"lang": lang_recarga, "titulo": titulo_recarga}
            if lang_recarga != idioma:
                fallos.append(f"{idioma}: tras recargar, <html lang> es {lang_recarga!r}")
            if titulo_recarga != titulo:
                fallos.append(
                    f"{idioma}: el título vuelve al del servidor tras recargar ({titulo_recarga!r}); "
                    "el <title> de metadata pisa al tuyo"
                )

        salida["consola"] = consola
        if consola:
            fallos.append(f"consola con {len(consola)} errores/avisos")
        navegador.close()

    print(json.dumps(salida, ensure_ascii=False, indent=2))
    if fallos:
        print("\nFALLOS:", file=sys.stderr)
        for f in fallos:
            print(f" - {f}", file=sys.stderr)
        return 1
    print("\nOK: idioma, título, persistencia y textos traducidos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
