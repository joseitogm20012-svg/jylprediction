# PRD — ScrapyCoco: Visual Scraper Administration Suite

## 1. Descripción General

ScrapyCoco es un panel web independiente para administrar, ejecutar y monitorear scrapers de datos futbolísticos del ecosistema JLY Predictor. Combina un backend FastAPI con un frontend HTML/CSS/JS vanilla, permitiendo ejecutar scrapers y ver logs en tiempo real sin usar la terminal.

## 2. Arquitectura

| Componente | Tecnología | Puerto |
|------------|-----------|--------|
| Backend API | FastAPI (Python 3.12+) | 3006 |
| Frontend | HTML5 + CSS3 + JS vanilla | 3006 (servido por FastAPI) |
| BD local | SQLite (`scrapycoco.db`) | — |
| Charts | Chart.js 4.4.1 (CDN) | — |

## 3. Scrapers Soportados (13)

| ID | Nombre | Tipo |
|----|--------|------|
| `results` | Actualizar Resultados | Script (subprocess) |
| `xg` | xG, Tiros y Centros (FBref - For) | Clase (FBrefScraper) |
| `xga` | xGA (FBref - Against) | Clase (FBrefScraper) |
| `cards` | Tarjetas y Faltas (FBref - Misc) | Clase (FBrefScraper) |
| `flashscore` | Flashscore Match Stats (Playwright) | Clase (FlashscoreScraper) |
| `transfermarkt` | Transfermarkt Squad Data (Playwright) | Clase (TransfermarktScraper) |
| `wc2026` | Datos Faltantes Mundial 2026 | Script (subprocess) |
| `elo` | Calcular Ratings Elo | Script (subprocess) |
| `shooting` | Tiros por Jugador (FBref - Shooting) | Script (subprocess) |
| `passing` | Asistencias y Pases (FBref - Standard) | Script (subprocess) |
| `keepers` | Porteros (FBref - Goalkeeping) | Script (subprocess) |
| `corners` | Córners por Equipo (FBref - Misc) | Script (subprocess) |
| `sofascore` | Estadísticas Avanzadas (Sofascore) | Clase (SofascoreScraper) |

## 4. Funcionalidades del Frontend

### 4.1 Tab de Extracción (Principal)
- **Grid de scrapers**: 13 tarjetas con nombre, descripción, estado, última ejecución
- **Checkbox por scraper**: selección múltiple para batch run
- **Ejecución individual**: botón por scraper con conexión SSE en vivo
- **Batch run**: ejecuta scrapers seleccionados secuencialmente con barra de progreso
- **Parámetros avanzados**: match_id, team_name, modo sandbox
- **Terminal web**: logs en tiempo real con filtros por nivel (system/error/success/info/warning)
- **Autoscroll**: toggle para seguir logs automáticamente
- **Preview modal**: vista previa de datos extraídos (solo class-based scrapers)
- **Badge de validaciones**: cuenta warnings de validación de datos

### 4.2 Tab de Historial
- **Lista de ejecuciones**: tabla con scraper, fecha, duración, estado
- **Filtro por scraper**: selector para filtrar historial
- **Métricas**: gráficos de torta (éxito/fallo) y barras (duración promedio)
- **Estadísticas globales**: total ejecuciones, tasa de éxito, promedio duración

### 4.3 Tab de Configuración
- **Transformaciones**: aplicar transformaciones a datos exportados
- **Exportación**: CSV / JSON / Excel con transforms opcionales
- **Diagnóstico**: modal para inspeccionar estructura HTML de scrapers

### 4.4 Tab de Programador (Scheduler)
- **Lista de tareas programadas**: scraper, cron, próxima ejecución, estado
- **CRUD completo**: agregar, pausar, reanudar, eliminar tareas
- **Ejecución manual**: botón "Run Now" por tarea

## 5. Endpoints del Backend

| Método | Ruta | Propósito | Tipo respuesta |
|--------|------|-----------|---------------|
| GET | `/api/scrapers` | Listar scrapers con estado | JSON |
| GET | `/api/run/{id}` | Ejecutar scraper (SSE) | SSE stream |
| POST | `/api/batch/run` | Ejecutar múltiples scrapers | SSE stream |
| GET | `/api/preview/{id}` | Vista previa de datos | JSON |
| POST | `/api/export` | Exportar datos (CSV/JSON/Excel) | Archivo |
| GET | `/api/history` | Historial de ejecuciones | JSON |
| GET | `/api/history/metrics` | Métricas agregadas | JSON |
| GET | `/api/history/stats` | Estadísticas globales | JSON |
| GET | `/api/scheduler/list` | Tareas programadas | JSON |
| POST | `/api/scheduler/add` | Agregar tarea | JSON |
| DELETE | `/api/scheduler/{id}` | Eliminar tarea | JSON |
| POST | `/api/scheduler/{id}/pause` | Pausar tarea | JSON |
| POST | `/api/scheduler/{id}/resume` | Reanudar tarea | JSON |
| POST | `/api/scheduler/{id}/run-now` | Ejecutar tarea manual | JSON |
| POST | `/api/diagnostic/run/{id}` | Diagnóstico HTML | JSON |
| GET | `/api/diagnostic/history/{id}` | Historial de snapshots | JSON |
| GET | `/api/diagnostic/compare/{id1}/{id2}` | Comparar snapshots | JSON |
| GET | `/` | Servir index.html | HTML |
| GET | `/style.css` | Servir CSS | CSS |
| GET | `/script.js` | Servir JS | JS |

## 6. Prioridad de Testing (TestSprite)

### 🔴 P0 — Funcionalidades Críticas (deben funcionar siempre)

| # | Escenario | Tipo |
|---|-----------|------|
| 1 | **Listar scrapers**: GET /api/scrapers retorna 8 scrapers con status idle | Backend |
| 2 | **Ejecutar scraper**: GET /api/run/{id} retorna SSE con event:start, logs, event:end | Backend |
| 3 | **Batch run**: POST /api/batch/run con 2+ IDs retorna SSE con batch-start/progress/end | Backend |
| 4 | **404 en scraper inválido**: GET /api/run/fake retorna 404 | Backend |
| 5 | **Servir frontend**: GET / retorna index.html con title "ScrapyCoco" | Frontend |
| 6 | **Grid de scrapers se renderiza**: 8 tarjetas visibles con botones | Frontend |
| 7 | **Selección múltiple**: checkboxes funcionan, contador se actualiza | Frontend |

### 🟡 P1 — Funcionalidades Importantes

| # | Escenario | Tipo |
|---|-----------|------|
| 8 | **Historial**: GET /api/history retorna array | Backend |
| 9 | **Métricas**: GET /api/history/metrics retorna datos | Backend |
| 10 | **Stats**: GET /api/history/stats retorna 200 | Backend |
| 11 | **Preview endpoint**: GET /api/preview/{id} retorna estructura columns/rows | Backend |
| 12 | **Export endpoint**: POST /api/export con format csv/json valida parámetros | Backend |
| 13 | **Scheduler list**: GET /api/scheduler/list retorna array | Backend |
| 14 | **Scheduler add/delete**: agregar y eliminar tarea | Backend |
| 15 | **Navegación por tabs**: Extracción ↔ Historial ↔ Configuración ↔ Programador | Frontend |
| 16 | **Terminal muestra logs**: al ejecutar scraper, aparecen líneas en la terminal | Frontend |

### 🟢 P2 — Funcionalidades Secundarias

| # | Escenario | Tipo |
|---|-----------|------|
| 17 | **Scheduler pause/resume**: pausar y reanudar tarea | Backend |
| 18 | **Scheduler run-now**: ejecutar tarea manualmente | Backend |
| 19 | **Diagnostic history**: GET /api/diagnostic/history/{id} retorna array | Backend |
| 20 | **Diagnostic compare**: GET /api/diagnostic/compare con IDs inválidos retorna 404 | Backend |
| 21 | **Parámetros avanzados**: match_id, team_name, sandbox se envían correctamente | Frontend |
| 22 | **Filtros de log**: cambiar nivel de log filta líneas visibles | Frontend |
| 23 | **Autoscroll**: toggle activa/desactiva scroll automático | Frontend |

## 7. Stack de Testing

```
Herramienta: TestSprite
Tipo: Backend (API) + Frontend (UI)
URL objetivo: http://localhost:3006
Auth: Ninguna
Framework tests: Python (requests + pytest)
```

## 8. Criterios de Aceptación

- Todos los P0 pasan sin errores
- Al menos 80% de P1 pasan
- 0 regresiones introducidas
- Timeout máximo por test: 30s (backend), 60s (frontend con preview)
