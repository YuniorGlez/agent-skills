# Dia (navegador) y computer use

Estado el 31-oct-2026: **Dia no se puede controlar por accesibilidad**. Hay que saberlo antes de
prometer nada.

## Síntoma exacto

```bash
agent-desktop snapshot --app Dia -i --compact
# {"ok":false,"error":{"code":"ACTION_NOT_SUPPORTED",
#  "message":"Renderer did not enable accessibility activation"}}
```

- `--surface menubar` **sí** funciona (1.199 refs): los menús nativos son accesibles.
- La ventana web (`--window-id`) y `list-surfaces` fallan igual o dan `AMBIGUOUS_TARGET`.
- cua-driver (`computer_use` capture ax) devuelve `0x0` y 0 elementos: no ve la ventana.
- Activar `AXManualAccessibility` desde fuera con ctypes (`scripts/ax-force-a11y.py <pid>`) devuelve
  `set=0` en el proceso principal y el renderer sigue sin activarse.

Dia corre sobre ArcCore (Chromium). El renderer no responde al pedido de accesibilidad web que hace
agent-desktop; no es un problema de permisos TCC (la app principal los tiene).

## Trampa: `launch` con Dia es ambiguo

```
launch "Dia" → AMBIGUOUS_TARGET, candidate_pids [638,1667,2473,6818]
```

Los `Browser Helper` de ArcCore cuentan como instancias de la app y `launch` no tiene flag de pid.
Workaround: abrir con el sistema y luego capturar:

```bash
open -b company.thebrowser.dia
agent-desktop list-windows --app Dia     # dos ventanas: una 0x0 (ignorar) y la real
```

## Vías para controlarlo

1. **`--force-renderer-accessibility` NO funciona (probado 31-oct-2026).** Con el flag puesto
   (`ps` lo confirma), el renderer sigue contestando «Renderer did not enable accessibility
   activation». Tampoco con `AXManualAccessibility` forzado desde fuera. Es la única app de esta
   máquina donde la accesibilidad está descartada de raíz.
2. **`--remote-debugging-port=9222` SÍ funciona y es la vía buena.** Dia es Chromium 156:
   `curl -s http://localhost:9222/json/version` responde, `PUT /json/new?<url>` abre pestaña y
   `cdp_eval.js --match <dominio>` evalúa JS en su DOM. Requiere cerrar el navegador una vez
   (restaura las pestañas solo). No hay que añadir el flag de accesibilidad: CDP no lo necesita.
3. `computer_use` con captura de pantalla y clics por coordenadas: funciona sin árbol
   (`capture app='screen'` da la pantalla compuesta y visión la describe), pero no permite leer el
   DOM ni verificar. Último recurso.

Detalle del flujo con LinkedIn: `linkedin-compose.md`.

## Lo que sí tiene Dia por dentro

`~/Library/Application Support/Dia/AgentServer/` contiene `tool-schemas/*.json` con un MCP de 105
herramientas (`mcp_version 2025-11-25`, `server_name dia`): `browser_use`, `open_tabs`, `read_tabs`,
`close_tabs`, `read_slack_channel`, `list_slack_channels`, Figma, Linear, Salesforce, Google Drive…
No hay tool de Discord y **no hay socket ni puerto escuchando**: ese MCP lo consume el agente interno
de Dia, no está expuesto al exterior. Si algún día lo exponen, sería la vía buena para leer pestañas.

## Alternativa práctica

Si el objetivo es leer Discord, se hace en `Discord.app` (ver `discord-desktop.md`) que expone el
árbol completo. Si el objetivo es leer una web concreta en Dia, CDP es más barato que la accesibilidad
incluso cuando esta funciona.
