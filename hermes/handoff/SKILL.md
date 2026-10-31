---
name: handoff
description: Compacta la conversación en un handoff para otro agente.
---

# Handoff — documento de traspaso entre agentes

Escribe un documento de handoff que resuma la conversación actual para que un agente fresco pueda continuar el trabajo. Guárdalo en el directorio de handoffs (`~/.hermes/handoffs/` o `/tmp` si es desechable) — **no en el workspace del proyecto**.

## Contenido del documento

1. **Contexto**: qué se está haciendo y por qué (1-2 párrafos).
2. **Estado actual**: qué está hecho, qué falta, dónde duele.
3. **Decisiones tomadas** y su razón, para no re-litigarlas.
4. **Próximos pasos**: lista ordenada de lo que queda.
5. **Sección "skills sugeridas"**: skills que el agente que retome debería invocar.
6. **Bloqueantes / riesgos**: cosas que pueden frenar al próximo agente.

## Reglas

- **No dupliques contenido** ya capturado en otros artefactos (specs, planes, ADRs, issues, commits, diffs). Refiérete a ellos por ruta o URL.
- **Redacta información sensible**: API keys, contraseñas, PII. Nunca incluyas secretos en crudo — apunta a dónde están gestionados (credential store, .env con nombre del archivo).
- Si el usuario pasa argumentos, trátalos como descripción de en qué se centrará la próxima sesión y adapta el documento.
- Escribe el documento como si el lector no supiera nada de esta conversación: autocontenido.

## Verificación

- [ ] ¿El documento es autocontenido para un agente fresco?
- [ ] ¿Referencia artefactos por ruta en vez de duplicar contenido?
- [ ] ¿Incluye la sección "skills sugeridas"?
- [ ] ¿Sin secretos ni PII en el documento?
- [ ] ¿Guardado en ~/.hermes/handoffs/ (o /tmp si es desechable)?
