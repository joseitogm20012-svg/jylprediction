---
name: lighthouse-ci
description: Lanza auditorías de rendimiento web y accesibilidad simulando navegación real. Usar para medir Core Web Vitals o antes de desplegar a producción.
compatibility: [opencode]
---

# Lighthouse CI

## Flujo
1. Ejecuta `npx lighthouse <url> --view` para auditoría individual.
2. Para CI: configura `lhci autorun` con umbrales en `.lighthouserc.js`.
3. Reporta métricas: FCP, LCP, TBT, CLS, accesibilidad, SEO.
4. Si alguna métrica no pasa el umbral, diagnostica causas y sugiere fixes.
