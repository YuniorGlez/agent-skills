---
name: idioma-interfaz-web
description: "Use cuando una web pase a tener varios idiomas."
version: 1.0.0
author: Hermes + el operador
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [frontend, next, i18n, idiomas, localStorage, a11y, playwright]
    related_skills: [tema-claro-oscuro-web, ai-assistant-websites, accesibilidad-wcag]
---

# Multi idioma en una app web (interfaz + asistente)

## When to Use

- «que la interfaz se pueda cambiar a inglés/alemán», «multi idioma», «i18n».
- Un asistente (chat o voz) que tiene que contestar en el mismo idioma que la interfaz.
- No es para decidir la paleta ni la tipografía: eso es `impeccable-design`.

## Lo primero: dónde vive la elección

Pregúntalo antes de escribir código, porque cambia la arquitectura entera:

| Guardado en | El servidor lo sabe | Coste |
|---|---|---|
| Cookie | sí | primera pintura correcta, `<html lang>`, metadatos y componentes de servidor traducidos sin convertirlos en cliente |
| `localStorage` | **no** | el idioma tiene que viajar en CADA petición que produce texto; primera pintura en el idioma por defecto y un parpadeo al corregir |

Si el usuario pide `localStorage` (frecuente: «como el tema»), acéptalo, pero dilo en la PR: el parpadeo es la consecuencia, no un descuido.

## Procedimiento

1. **Inventario de textos, en dos columnas.** Antes de traducir, lista lo que pinta el CLIENTE y lo que
   compone el SERVIDOR. Lo que se olvida siempre es lo segundo: títulos y etiquetas que devuelve una
   herramienta, frases que lee la voz, mensajes de error de las rutas de API. Si solo traduces componentes,
   el panel del servidor se queda en el idioma antiguo.
2. **Un módulo base sin React y sin base de datos** (`lib/idioma.ts`): tupla de idiomas, tipo, locale de
   `Intl`, `euros()`/`fecha()`/`dias()`, y la etiqueta visible de cada estado. Lo importan servidor y
   navegador; con `"use client"` el prompt y las herramientas no podrían usarlo.
3. **Diccionario de interfaz con un TIPO, no `Partial`** (`lib/i18n.ts`): `type TextosUI = {...}` y
   `Record<Idioma, TextosUI>`. Si a un idioma le falta una clave, no compila. Lo que cambia de orden entre
   idiomas (plurales, «X e Y») va como FUNCIÓN, no como plantilla con `replace`: en alemán el verbo se va al
   final y concatenar trozos produce frases malas.
4. **Frases del servidor aparte** (`lib/textos-asistente.ts`): funciones por idioma para la frase que la voz
   puede afirmar, los títulos de la ficha, sus etiquetas y los errores que ve la persona. Los mensajes de
   validación de Zod pueden quedarse en un idioma: los lee el modelo, no la persona, y los reformula.
5. **El idioma viaja en cada petición que produce texto**: chat, token de voz, herramienta de voz. En Zod,
   `idioma: z.enum(IDIOMAS).default(IDIOMA_POR_DEFECTO)`. En un token de sesión (Gemini Live), el idioma va
   al acuñarlo y queda BLOQUEADO: las instrucciones las sigue fijando el servidor, no el navegador.
6. **Prompt por idioma.** Un prompt en español que pide «habla en inglés» se degrada al alargar la
   conversación. Traduce las instrucciones enteras y añade la regla de que se contesta en el idioma elegido
   aunque la persona escriba en otro.
7. **`<html lang>` antes de pintar**, con script en línea como primer hijo del `<body>` y
   `suppressHydrationWarning` en el `<html>` (idéntico al truco del tema). Solo acepta idiomas conocidos.
8. **El título de la pestaña:** NO uses `document.title` en un `useEffect`. Next rehidrata su `<title>` de
   `metadata` después de los efectos y lo devuelve al idioma del servidor en cada recarga (se ve como «el
   título cambia al pulsar pero vuelve al recargar»). Quita `title` de `metadata` y renderiza
   `<title>{t.tituloDocumento}</title>` desde el proveedor de cliente: React 19 lo sube al `<head>` y lo
   actualiza como cualquier texto.
9. **Datos contra etiquetas.** Nombre, ciudad, sector, notas y el valor interno del estado (`activo`,
   `moroso`) no se traducen NUNCA: se guardan y se pintan tal cual. Se traduce la etiqueta visible del estado,
   el formato de importes y fechas, y las frases del servidor. Los textos que van a agentes (`llms.txt`,
   catálogo de herramientas) se quedan como están.
10. **Gate y prueba real**: `bun run check` / `npm run check`, `build`, y `scripts/verificar-idioma.py`
    contra el servidor. Un «lo he traducido todo» no es prueba.

## Pitfalls

- **Traducir solo el cliente y dar la ficha por hecha.** El panel que compone el servidor se queda en el
  idioma viejo; es lo que más canta y lo que menos se nota al leer el código.
- **`document.title` en efecto** (ver punto 8). Y ojo: `h1` traducido con título de pestaña sin traducir es el
  síntoma exacto de que el `<title>` de `metadata` está pisando el tuyo.
- **Server Components que se vuelven cliente enteros.** Con `localStorage` el texto es de cliente, pero los
  DATOS no: deja `page.tsx` de servidor trayendo números y mete solo el texto en componentes de cliente
  (`Cabecera`, `ResumenCartera`).
- **`useCallback` con el diccionario fuera de las dependencias.** `t` cambia de identidad al cambiar de
  idioma: si no va en el array, se queda con el diccionario anterior en los mensajes de error.
- **Formatear importes a mano.** `Intl.NumberFormat` con el locale del idioma; el mismo dato se lee
  «1.234 €» o «1,234 €», y en voz alta eso es otro número.
- **Arrancar el estado con el valor del `localStorage`** para «evitar el parpadeo»: rompe la hidratación.
  Empieza en el idioma por defecto y corrige en `useEffect`, como el tema.
- **Conflicto con la PR del tema.** Las dos tocan cabecera y `layout.tsx`. Deja un hueco (`children`) en el
  componente de cabecera para que el otro selector se añada con una línea, y avísalo en la PR.

## Verificación que vale

`scripts/verificar-idioma.py` (Playwright, `python3`): cambia de idioma en el
navegador real y comprueba `<html lang>`, título, persistencia tras recarga (también el título), que no queden
cadenas de la interfaz anterior (lista de palabras que solo existen en ese idioma) y consola limpia. Sale con
código ≠ 0 si algo falla.

```bash
python3 scripts/verificar-idioma.py --url http://localhost:3103 --idiomas es,en,de
```

Complemento imprescindible en servidor, con `curl`: la misma herramienta pedida con `idioma=en` y `idioma=de`
para ver que la frase y las etiquetas salen traducidas y los datos iguales; el token de voz con y sin cuerpo;
un idioma desconocido (`fr`) para ver que cae al de por defecto.
