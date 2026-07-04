---
name: query-optimizer
description: Revisa sentencias SQL y modelos ORM para añadir índices y evitar problemas de N+1. Usar cuando consultas sean lentas o haya múltiples queries anidadas.
compatibility: [opencode]
---

# Query Optimizer

## Flujo
1. Identifica queries lentas mediante `EXPLAIN ANALYZE` o logs de base de datos.
2. Detecta patrones N+1 en bucles de ORM (SQLAlchemy, Prisma, Django ORM).
3. Agrega índices compuestos en columnas filtradas frecuentemente.
4. Sugiere `select_related` / `prefetch_related` o `JOIN` tempranos.
