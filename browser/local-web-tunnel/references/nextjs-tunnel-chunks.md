# Next dev + túnel trycloudflare — 403 en chunks JS (página muerta en móvil)

Caso: X-Signal :3059, 14-ago-2026 (verificado con curl real a través del túnel).

## Síntoma
El HTML de la página llega perfecto a través del túnel, pero NADA es clickeable en el móvil:
el dev server de Next bloquea con 403 cualquier request con header `Origin` que no sea
localhost (protección anti-CSRF del dev server), y Next pone `crossorigin` en sus `<script>`
→ los chunks de `/_next/static/chunks/*.js` devuelven 403 a través del túnel → React nunca
hidrata. El HMR websocket da "Unauthorized" igual.

## Fix obligatorio ANTES de dar el link
```ts
// next.config.ts
const nextConfig: NextConfig = {
  allowedDevOrigins: ["*.trycloudflare.com"],  // wildcard: el subdominio cambia en cada relanzamiento
  ...
};
```
Requiere REINICIAR el dev server (un server ya arrancado no recarga next.config).

## Verificación mínima del túnel (no solo el 200 de la página)
```bash
T=<url-trycloudflare>
curl -s -o /dev/null -w '%{http_code}' $T/                 # página: 200
CHUNK=$(curl -s $T/ | grep -o '/_next/static/chunks/[^"]*\.js' | head -1)
curl -s -o /dev/null -w '%{http_code}' $T$CHUNK            # chunk: 200 (si 403 → página muerta)
curl -s -o /dev/null -w '%{http_code}' $T/api/state        # API: 200 (datos client-side)
```

## Contexto
- Pitfall original documentado 13-ago-2026 (caso landing-creditos) en skill
  `la agencia-webapp-bootstrap` → Pitfalls → «Next dev + túnel trycloudflare → 403 en chunks JS».
- Aplica SOLO a `bun run dev` / `next dev`: `next start` (producción) no tiene ese filtro de
  Origin, así que un build + start también evita el problema.
