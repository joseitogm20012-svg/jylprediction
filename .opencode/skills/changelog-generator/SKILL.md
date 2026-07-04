---
name: changelog-generator
description: Lee el historial de Git y genera un historial de cambios estructurado. Usar antes de releases o para mantener CHANGELOG.md actualizado.
compatibility: [opencode]
---

# Changelog Generator

## Flujo
1. Lee commits desde el último tag con `git log --oneline --no-decorate`.
2. Clasifica por tipo: `feat`, `fix`, `docs`, `refactor`, `chore` (conventional commits).
3. Ordena secciones: Features → Bug Fixes → Performance → Docs.
4. Genera entrada en `CHANGELOG.md` con fecha y versión.
