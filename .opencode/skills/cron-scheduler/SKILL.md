---
name: cron-scheduler
description: Configura expresiones CRON complejas para tareas en segundo plano y las documenta. Usar al programar tareas periódicas o recordar sintaxis CRON.
compatibility: [opencode]
---

# Cron Scheduler

## Flujo
1. Traduce requerimientos humanos ("cada 6 horas") a expresión CRON (`0 */6 * * *`).
2. Usa `crontab.guru` para verificar la expresión antes de implementar.
3. En código, prefiere APScheduler, Celery Beat o cron nativo del sistema.
4. Documenta cada tarea: qué hace, frecuencia, dependencias, logs.
