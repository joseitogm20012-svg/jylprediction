---
name: self-healing-loop
description: Ejecuta un bucle repetitivo de prueba y error para corregir fallos de código automáticamente. Usar cuando el código falle, los tests no pasen o el usuario pida reparar un bug persistente.
compatibility: [opencode]
---

# Bucle de Autorreparación (Self-Healing Loop)

## Objetivo de la Skill
Corregir errores de código mediante un ciclo cerrado de ejecución de comandos, análisis de errores y refactorización, sin intervención del usuario, hasta que todas las pruebas pasen al 100%.

## Instrucciones Críticas del Flujo (Algoritmo en Bucle)

Por cada iteración del problema, debes seguir estrictamente estos 5 pasos de forma repetitiva:

1. **EJECUTAR**: Lanza el comando de pruebas o ejecución del proyecto (ej. `npm test`, `pytest`, `cargo test`) para capturar el estado actual.
2. **EVALUAR**: Si el comando tiene éxito (Exit Code 0), el bucle termina con éxito. Si falla, captura TODO el log de error de la terminal.
3. **DIAGNOSTICAR**: No adivines el parche. Abre y lee el archivo exacto donde se originó el error. Explica la causa raíz en una línea.
4. **REPARAR**: Modifica el código implementando la solución más sólida y limpia posible.
5. **REPETIR**: Regresa inmediatamente al Paso 1 utilizando el nuevo código modificado.

## Reglas de Escape del Bucle
- **Límite de intentos**: Detén el bucle tras 5 iteraciones fallidas consecutivas para evitar consumo excesivo de tokens.
- **Intervención**: Si alcanzas el límite, muestra un resumen de las 5 hipótesis fallidas y pide ayuda humana.
