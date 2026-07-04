---
name: memoize-expert
description: Optimiza renderizados de React aplicando useMemo y useCallback solo donde se necesita. Usar cuando haya renders innecesarios o lentitud en componentes.
compatibility: [opencode]
---

# Memoize Expert

## Flujo
1. Identifica componentes que renderizan sin cambios de props con React DevTools profiler.
2. Aplica `React.memo()` en componentes puros con props estables.
3. Envuelve funciones callback en `useCallback` y cálculos pesados en `useMemo`.
4. NO memoices por defecto — solo donde el profiling muestre beneficio medible.
