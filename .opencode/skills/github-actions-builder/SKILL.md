---
name: github-actions-builder
description: Crea tuberías de integración y despliegue continuo (CI/CD) sin errores de sintaxis. Usar al configurar GitHub Actions para testeo o deploy.
compatibility: [opencode]
---

# GitHub Actions Builder

## Flujo
1. Define triggers (`push`, `pull_request`, `workflow_dispatch`).
2. Configura matrix de versión de lenguaje/OS si aplica.
3. Cachea dependencias (npm, pip, Docker layers).
4. Separa jobs: lint → test → build → deploy. Usa `actions/upload-artifact` entre stages.
