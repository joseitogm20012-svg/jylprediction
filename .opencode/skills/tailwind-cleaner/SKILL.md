---
name: tailwind-cleaner
description: Reorganiza y optimiza clases de Tailwind CSS eliminando redundancias visuales. Usar cuando haya clases duplicadas o estilos en conflicto.
compatibility: [opencode]
---

# Tailwind Cleaner

## Flujo
1. Agrupa clases por categoría (layout, tipografía, color, spacing) usando `@apply` o plugins.
2. Elimina clases que son anuladas por otras posteriores (ej. `p-4 p-6` → `p-6`).
3. Extrae combinaciones repetidas en componentes reutilizables.
4. Aplica `prettier-plugin-tailwindcss` para orden consistente.
