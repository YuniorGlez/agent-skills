# Buscar tendencias y reacciones en X/Twitter vía xurl (verificado ago 2026)

Cuando la investigación necesita ver qué dice la comunidad de X sobre un tema
(trending methodology, reacciones a un post, críticos influyentes), `xurl` da
acceso autenticado a la API v2 de X sin CAPTCHA (mejor que Nitter, que está caído
la mayoría del tiempo).

## Comandos probados

```bash
# Búsqueda reciente por frase exacta, en inglés, con métricas + autor resuelto
xurl --auth oauth2 "/2/tweets/search/recent?query=%22gauntlet%20loop%22%20lang%3Aen&max_results=20&tweet.fields=public_metrics,created_at,author_id,conversation_id&expansions=author_id,referenced_tweets.id&user.fields=username"
```

- **`max_results` debe estar entre 10 y 100** (5 → 400 Invalid Request).
- Añadir `expansions=author_id` + `user.fields=username` y construir el mapa
  `{id: username}` desde `includes.users` para saber quién tuitea.
- `from:<usuario> "frase"` → los posts ORIGINALES de un crítico concreto
  (ej. `from:levelsio "gauntlet loop"`), clave para triangulación.
- Los `RT @user:` en el texto indican retweets → el original es de otro autor;
  buscar el `referenced_tweets` para localizar al autor original.
- Ordenar hallazgos por `public_metrics.retweet_count/like_count` para identificar
  las voces que mueven la conversación (tanto a favor como críticas).
- Combinar con HN Algolia (`hn.algolia.com/api/v1/search?query=...`) para la
  discusión técnica de la comunidad dev.

## Patrón de triangulación de un trend

1. HN Algolia: story + comments del tema (fuente primaria si es algo publicado).
2. xurl search `"<término>" lang:en` → reacciones recientes, ejemplos reales.
3. `from:<autor-origen> <término>` → el post canónico del creador.
4. `from:<detractor> <término>` → la crítica más seria (no descartarla).
5. Sintetizar: qué es, de dónde viene, qué funciona, qué critican, costes reales.
