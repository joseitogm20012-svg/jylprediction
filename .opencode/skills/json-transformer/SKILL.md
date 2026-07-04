---
name: json-transformer
description: Mapea, filtra y convierte grandes volúmenes de datos JSON mediante scripts rápidos. Usar al transformar datos entre APIs o limpiar respuestas.
compatibility: [opencode]
---

# JSON Transformer

## Flujo
1. Lee JSON de archivo o stdin. Identifica estructura y campos clave.
2. Usa `jq` para filtros rápidos en terminal o Python `json` module para lógica compleja.
3. Mapea campos: rename, transform types, anidar/desanidar.
4. Valida salida contra schema esperado. Output a archivo o stdout.
