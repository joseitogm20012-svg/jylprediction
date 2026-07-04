---
name: swagger-doc-gen
description: Genera especificaciones OpenAPI/Swagger leyendo directamente los controladores del backend. Usar para documentar APIs REST automáticamente.
compatibility: [opencode]
---

# Swagger Doc Gen

## Flujo
1. Usa decoradores/anotaciones del framework (FastAPI, NestJS, DRF) para inferir schemas.
2. Asegura que cada endpoint tenga `summary`, `description` y ejemplos de respuesta.
3. Agrupa endpoints por tags. Documenta códigos de error (400, 401, 404, 500).
4. Verifica que el schema generado sea válido con `swagger-cli validate`.
