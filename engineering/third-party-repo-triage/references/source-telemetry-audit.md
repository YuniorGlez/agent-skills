# Auditoría de telemetría/exfiltración en código fuente (playbook)

Auditoría exhaustiva de un repo (caso validado: browser Rust ~50 crates, autor
Lexmount) buscando canales de telemetría, exfiltración o comunicación saliente
no explícita hacia dominios de terceros. Solo lectura: NO ejecutar nada del
repo. Resultado del caso real: SIN canales; todos los candidatos resultaron
benignos (ver tabla abajo). El valor del playbook es la escalera ordenada +
la taxonomía de falsos positivos verificada.

## Escalera de verificación (en orden)

### 0. Dominio sospechoso primero
```bash
rg -n 'lexmount'                    # en TODO el árbol
rg -n 'browser\.lexmount|lexmount\.com'
```
Coincidencias solo en fixtures de tests/datos (p.ej. `github.com/lexmount/...`
en `compare.test.mjs`) NO son riesgo. 0 matches en código fuente = evidencia
positiva a reportar.

### 1. Keywords amplias
`telemetry|analytics|phone.?home|update.?check|usage.?report|report.?usage|collect_usage`
Casi todos los hits serán maquinaria interna del producto. Verificar el
contexto de CADA uno antes de declararlo riesgo.

### 2. URLs hardcodeadas (search_files no excluye dirs ni pagina bien → usar rg)
```bash
rg -n --glob '*.rs' \
  -g '!**/tests/**' -g '!**/tests.rs' -g '!**/test_support/**' \
  -g '!**/moli-test-support/**' -g '!vendor/**' -g '!third_party/**' -g '!target/**' \
  'https?://[a-zA-Z0-9._-]+' \
  | grep -v -E 'w3\.org|mozilla\.org|example\.(com|test|org|net)|127\.0\.0\.1|localhost|whatwg\.org|servo|rust-lang\.org|drafts\.csswg|tc39\.es|chromium\.org|searchfox\.org|spec\.whatwg'
```
El resto, revisarlo manualmente: namespaces XML (w3.org), headers de licencia
MPL (mozilla.org) y dominios `.test` en `#[cfg(test)]` son benignos.

### 3. Env vars — enumerarlas TODAS y clasificar
```bash
rg -o --no-filename --glob '*.rs' -g '!**/tests/**' -g '!**/tests.rs' -g '!vendor/**' '"MOLI_[A-Z0-9_]+"' | sort -u
rg -n --glob '*.rs' 'env::var\(|env::var_os\(|std::env::var'
```
Clasificar cada una: toggle de debug local (tracing, probes, perfiles) /
flag de feature local vs algo que habilita red. El manejo estándar de
`http_proxy`/`https_proxy`/`no_proxy` es configuración del usuario, no telemetría.

### 4. Identificadores en peticiones salientes
- **UA por defecto**: `grep DEFAULT_USER_AGENT` — un Chrome genérico sin token
  (`Chrome/145.0.0.0`) es OK; un token `App/1.0` sería identificador único.
- **Sec-CH-UA brands**: derivadas del UA (greased + Chromium) = comportamiento
  normal de Chromium, no marca propia.
- **Headers por defecto**: `default_request_headers: Vec::new()` = OK. Buscar
  `X-App-*`, headers con versión o `set_user_agent_suffix` que se aplique solo.
- Tokens tipo `Moli/...` encontrados: verificar con `sed -n` el contexto —
  suelen estar dentro de `#[test]` (valor test-only).

### 5. Pantalla de dependencias
```bash
rg -n 'update-informer|self_update|self-update|notify-rust|heim|sysinfo' Cargo.lock
rg -n 'sentry|opentelemetry|analytics|telemetry|posthog|mixpanel|amplitude|segment|influx|datadog' --glob Cargo.toml
rg -n 'reqwest|ureq|\bhyper\b|awc' --glob Cargo.toml   # clientes HTTP alternativos
```

### 6. Sockets, binds y arranque
```bash
rg -n -g '!**/tests/**' -g '!**/tests.rs' 'TcpStream::connect|SocketAddr::new\(|Ipv4Addr::new\(|Ipv6Addr::new\('
rg -n 'TcpListener|\.bind\(|127\.0\.0\.1|0\.0\.0\.0'   # binds por defecto loopback = OK
rg -n 'spawn|block_on' <binario principal>/*.rs        # ¿peticiones salientes al arrancar?
```
- Flags del CLI: leer cli.rs completo (clap). Flags de auth/telemetría pueden
  existir pero estar rechazados como no implementados (`reject_unsupported_*`)
  → reportar igual (no hay canal).
- Navegación por defecto: `about:blank` = OK; un `start_url` fijo = sospechoso.

### 7. Build-time vs runtime
`build.rs` de vendors (p.ej. deno rusty_v8): descarga de binarios en tiempo de
COMPILACIÓN desde `github.com/denoland/rusty_v8/releases` con override
`RUSTY_V8_MIRROR`/`RUSTY_V8_ARCHIVE`. No es telemetría runtime; anotarlo en el
informe como severidad "baja" para exhaustividad.

### 8. Harness de dev (no embebido en el binario)
```bash
rg -n 'https?://[a-zA-Z0-9.-]+' scripts/ tools/ moli-benchmark/ moli-playground/ | grep -v -E 'example\.(com|test)|127\.0\.0\.1|localhost|w3\.org'
```
URLs públicas como objetivos de tests/demos (phys.org, ifeng.com, chatgpt.com…)
= dev-only, no se ejecutan en runtime del producto distribuido.

## Taxonomía de falsos positivos (verificada en el caso real)

| Patrón sospechoso | Qué es realmente |
|---|---|
| módulo `telemetry` (p.ej. `moli/src/telemetry.rs`) | Logger local `tracing_subscriber` → stderr, sin red |
| `update_check` en service workers | Maquinaria del spec web `registration.update()` (consulta el script del PROPIO origen), no auto-update del binario |
| `metrics` | Métricas de layout del motor de render |
| `report`/`collect` en SW runtime | CSP reports / diagnósticos de cookies internos |
| `DocumentCookieFacadeTelemetrySnapshot` | Snapshot interno expuesto solo vía CDP al cliente conectado localmente |
| `navigator.sendBeacon` | Implementación de la API web estándar (la invoca JS de la página), no beacon propio del navegador |
| `Tracing.dataCollected` (dominio CDP) | Eventos del protocolo CDP estándar hacia el cliente conectado |
| vars `MOLI_*` (tracing/probes) | Toggles de depuración local, sinks = logs/eventos CDP |
| URLs en scripts/, playground/, benchmark/ | Objetivos de test de harness de dev, no embebidos |
| descargas en vendor build.rs | Build-time desde GitHub del upstream (denoland), overridable por env |

## Formato del informe final

Cada hallazgo: `archivo:línea` + contexto corto + severidad (info/baja/media/
alta) + descripción. Incluir los hallazgos verificados-benignos como "info" —
demuestran que se verificó cada candidato y blindan el veredicto. Cerrar con
veredicto explícito ("NO HAY canales de telemetría" + evidencia numerada). Si
el cliente dio un contrato JSON de salida (schema machine-validated),
cumplirlo exactamente (fence ```json permitido, sin prosa fuera).

## Caso real de referencia: moli (browser headless Rust, Lexmount)

- `lexmount.com`/`browser.lexmount` en todo el árbol: **0 matches** (solo
  `github.com/lexmount/moli-dark` en fixtures de tests del benchmark).
- `moli/src/telemetry.rs`: nombre engañoso, solo logger local a stderr.
- UA por defecto: Chrome 145 genérico sin token; `default_request_headers`
  vacío; tokens `Moli/*` solo en `#[test]`.
- 19 env vars `MOLI_*`: toggles de debug local; flags `web_bot_auth_*`
  rechazados como no implementados.
- Sin crates de updater/analytics/HTTP alternativo en Cargo.lock/Cargo.toml.
- Única descarga: V8 precompilado en build-time (github.com/denoland).
- Servidores bindeados a `127.0.0.1` por defecto; arranque sin peticiones
  salientes; navegación por defecto `about:blank`.
- Veredicto: SIN canales de telemetría, exfiltración ni comunicación saliente
  no explícita.
