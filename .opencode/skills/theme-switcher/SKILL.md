---
name: theme-switcher
description: Implementa sistemas de modo oscuro/claro consistentes usando variables CSS nativas. Usar al añadir soporte de temas al proyecto.
compatibility: [opencode]
---

# Theme Switcher

## Flujo
1. Define paleta en variables CSS:`--bg-primary`, `--text-primary`, etc.
2. Usa `prefers-color-scheme` para el tema por defecto y clase `.dark` para toggle manual.
3. Guarda preferencia en `localStorage` y aplica antes del render para evitar flash.
4. Todos los colores en componentes usan `var(--*)` — sin colores hardcodeados.
