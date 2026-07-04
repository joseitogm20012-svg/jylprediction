---
name: svg-optimizer
description: Limpia archivos SVG de metadatos basura y los convierte en componentes reutilizables. Usar al añadir iconos o ilustraciones SVG al proyecto.
compatibility: [opencode]
---

# SVG Optimizer

## Flujo
1. Pasa SVG por `svgo` para eliminar metadatos, editors comments y nodos vacíos.
2. Extrae colores a variables CSS o props del componente.
3. Convierte a componente React/Vue inline si se usa frecuentemente.
4. Verifica que `viewBox` esté presente y el SVG sea responsive.
