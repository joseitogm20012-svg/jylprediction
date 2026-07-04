---
name: lazy-loader
description: Identifica componentes e imágenes pesadas para aplicar división de código automática. Usar cuando el bundle inicial sea grande o haya componentes fuera de vista.
compatibility: [opencode]
---

# Lazy Loader

## Flujo
1. Escanea importaciones estáticas de componentes grandes (gráficas, tablas, mapas).
2. Convierte a `React.lazy()` + `Suspense` o `dynamic()` en Next.js.
3. Aplica `loading="lazy"` en imágenes y `IntersectionObserver` para componentes.
4. Verifica con Lighthouse que el LCP mejoró.
