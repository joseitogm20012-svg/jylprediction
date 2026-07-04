---
name: prisma-migrator
description: Diseña esquemas de bases de datos relacionales y gestiona migraciones sin pérdida de datos. Usar al modelar DB con Prisma o modificar esquemas existentes.
compatibility: [opencode]
---

# Prisma Migrator

## Flujo
1. Define modelos en `schema.prisma` con tipos correctos y relaciones.
2. Usa `prisma migrate dev` para desarrollo y `prisma migrate deploy` en producción.
3. Agrega índices en campos filtrados (`@@index`). Usa `@updatedAt` para timestamps.
4. Para cambios destructivos, genera migraciones SQL manuales con `prisma migrate create`.
