---
name: jsdoc-writer
description: Añade comentarios de tipo estructurados (JSDoc/TSDoc) a funciones para mejorar el autocompletado. Usar en código JavaScript/TypeScript no documentado.
compatibility: [opencode]
---

# JSDoc Writer

## Flujo
1. Por cada función pública: `@param` con tipo y descripción, `@returns` con tipo.
2. Usa `@throws` si lanza excepciones y `@example` para casos de uso.
3. En TypeScript, prefiere tipos inline en firma, JSDoc solo para lógica compleja.
4. Ignora funciones internas/helpers privados — documenta la API pública.
