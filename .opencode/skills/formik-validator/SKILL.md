---
name: formik-validator
description: Estructura formularios complejos con validaciones estrictas usando Yup o Zod. Usar al crear formularios con múltiples campos y reglas de validación.
compatibility: [opencode]
---

# Formik Validator

## Flujo
1. Define schema de validación con Yup/Zod: tipos, required, min/max, regex.
2. Conecta con Formik o React Hook Form usando `validationSchema` o `resolver`.
3. Muestra errores por campo con `touched` para evitar errores prematurios.
4. Validación en blur + submit. Soporta campos anidados y arrays.
