---
name: i18n-translator
description: Gestiona diccionarios de idiomas en JSON extrayendo cadenas de texto automáticamente. Usar al añadir internacionalización o sincronizar traducciones.
compatibility: [opencode]
---

# i18n Translator

## Flujo
1. Escanea el código en busca de strings visibles al usuario (etiquetas, títulos, botones).
2. Extrae a archivos JSON por idioma (`en.json`, `es.json`).
3. Usa claves anidadas por módulo (`auth.login.title`, `cart.checkout.button`).
4. Marca traducciones faltantes con placeholder y genera reporte de coverage.
