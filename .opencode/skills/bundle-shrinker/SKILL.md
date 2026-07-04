---
name: bundle-shrinker
description: Analiza dependencias de Node/Python para reducir el peso final del empaquetado. Usar cuando el bundle sea grande o se necesite optimizar tamaño de producción.
compatibility: [opencode]
---

# Bundle Shrinker

## Flujo
1. Corre `npm ls --all` o `pip freeze` para listar dependencias.
2. Identifica paquetes duplicados, no utilizados o pesados con `source-map-explorer` / `pip-check`.
3. Sugiere reemplazos (`lodash` → métodos individuales, `moment` → `date-fns`).
4. Aplica tree-shaking y code splitting si es frontend.
