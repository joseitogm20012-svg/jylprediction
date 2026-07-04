---
name: env-validator
description: Asegura que el archivo .env.example esté sincronizado y que no se filtren credenciales. Usar antes de commits o al agregar nuevas variables de entorno.
compatibility: [opencode]
---

# Env Validator

## Flujo
1. Compara `.env.example` contra el uso real en el código (grep de `os.environ`, `process.env`).
2. Agrega variables faltantes a `.env.example` con placeholder descriptivo.
3. Marca variables sin valor por defecto como `(obligatorio)`.
4. Revisa que `.env` esté en `.gitignore`. Advierte si hay secrets hardcodeados.
