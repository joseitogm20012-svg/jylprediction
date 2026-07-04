---
name: docker-architect
description: Genera archivos Dockerfile y docker-compose multi-etapa optimizados y seguros. Usar al contenerizar aplicaciones nuevas o mejorar imágenes existentes.
compatibility: [opencode]
---

# Docker Architect

## Flujo
1. Usa builds multi-etapa para separar dependencias de build de las de runtime.
2. Minimiza capas combinando `RUN` commands relacionados.
3. Prefiere imágenes base ligeras (`alpine`, `slim`). No corre como root.
4. Genera `.dockerignore` y `docker-compose.yml` con healthchecks.
