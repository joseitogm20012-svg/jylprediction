# Fase 3 — Validación + Scheduler + Diagnóstico

## Decisiones del usuario
- **Scheduler**: Flatpickr (CDN) para selector de fecha/hora
- **Diagnóstico**: Genérico para todos los scrapers
- **Validación inline**: Panel lateral (siempre visible mientras hay warnings activos)

---

## 📦 Nuevos Archivos

### 1. `scrapycoco/scheduler.py` — Programador de Tareas
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
```

Responsabilidades:
- `start_scheduler()` — arranca al startup de la app
- `add_job(scraper_id, cron_expression, params)` — agrega job a APScheduler + guarda en DB
- `remove_job(job_id)` — elimina job
- `list_jobs()` — retorna lista de jobs activos + sus estados (next_run_time, etc.)
- `pause_job(job_id)` / `resume_job(job_id)`
- Callback interno: ejecuta scraper vía `asyncio.to_thread(scraper_instance.run, **kwargs)`, guarda resultado en `execution_history`

Tabla `schedules` ya existe en `db.py` (de Fase 1). Se completa:
- `cron_expression` — string cron estándar
- `params` — JSON con `{match_id, team_name, sandbox}`
- `enabled` — 0/1

### 2. `scrapycoco/diagnostic.py` — Detección de Cambios Estructurales
Responsabilidades:
- `take_snapshot(soup, url)` → extrae estructura de la página:
  - Clases CSS que contienen palabras clave (`row`, `table`, `tab`, `player`, `lineup`, `stat`, `odds`, `name`, `value`, `category`)
  - Cantidad de tablas, tabs, filas por tabla
  - Labels de tabs encontrados
  - IDs importantes
  - Hash del HTML completo (para detección de cambio genérico)
- `compare_snapshots(old, new)` → retorna `StructureDiff`:
  - Selectores que desaparecieron (🔴 crítico)
  - Clases hash que cambiaron (🟡 warning)
  - Estructura que cambió (número de tabs/tablas)
  - Hash diferente (🟡 posible cambio)
- `store_snapshot(scraper_id, url, snapshot)` — guarda en tabla `structure_snapshots`
- `get_last_snapshot(scraper_id, url)` — recupera último snapshot
- `SnapShot` / `StructureDiff` — dataclasses/Pydantic models

Tabla nueva en `db.py` (en `init_db()`):
```sql
CREATE TABLE IF NOT EXISTS structure_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scraper_id TEXT NOT NULL,
    url TEXT,
    snapshot TEXT NOT NULL,  -- JSON con estructura
    html_hash TEXT,
    created_at TEXT NOT NULL
);
```

---

## 📝 Archivos Modificados

### 3. `scrapycoco/scrapers/base.py`
- Nuevo flag `self.validation_errors: list[dict] = []`
- Nuevo método `validate_and_report(row, scraper_id)`:
  - Aplica `VALIDATION_RULES[scraper_id]` a la fila
  - Por cada violación, agrega a `self.validation_errors` y emite `structured_log("validation_warning", ..., row=N, field="...", value="...", suggestion="...", severity="error|warning")`
  - NO interrumpe el flujo — solo marca
- Nuevo método `run_diagnostic(url, page_source)`:
  - Parsea con BeautifulSoup
  - Llama a `diagnostic.take_snapshot()`
  - Compara con último snapshot de esa URL
  - Emite `structured_log("diagnostic", ...)` si hay cambios
- `run()` propaga `preview` y `sandbox` a los métodos internos

### 4. `scrapycoco/main.py`
**Scheduler endpoints:**
| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/scheduler/list` | Lista tareas activas + inactivas con próxima ejecución |
| `POST` | `/api/scheduler/add` | `{scraper_id, cron, params?}` → agrega job |
| `DELETE` | `/api/scheduler/{id}` | Elimina tarea |
| `POST` | `/api/scheduler/{id}/pause` | Pausa tarea |
| `POST` | `/api/scheduler/{id}/resume` | Reanuda tarea |
| `POST` | `/api/scheduler/{id}/run-now` | Ejecuta inmediatamente |

**Diagnostic endpoints:**
| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/diagnostic/run/{scraper_id}` | Body: `{url, page_source?}` → ejecuta diagnóstico |
| `GET` | `/api/diagnostic/history/{scraper_id}` | Historial de snapshots |
| `GET` | `/api/diagnostic/compare/{id1}/{id2}` | Diff entre dos snapshots |

**SSE upgrade:**
- Nuevo evento `validation-error` con payload completo
- Nuevo evento `diagnostic` con snapshots/diffs

### 5. `scrapycoco/db.py`
- `init_db()` extiende con `CREATE TABLE IF NOT EXISTS structure_snapshots`
- Nuevas funciones: `save_snapshot()`, `get_snapshots()`, `get_snapshot()`, `get_latest_snapshot()`

### 6. `scrapycoco/index.html`
**Tab nav se expande a 4:**
```
⚡ Extracción | 📊 Historial | ⏰ Programador | ⚙️ Configuración
```

**Tab "Programador" contiene:**
- Sección "➕ Nueva Tarea Programada":
  - Selector de scraper (dropdown con todos)
  - Parámetros (match_id, team_name, sandbox)
  - Selector de frecuencia (Una vez / Cada hora / Cada día / Semanal / Personalizado)
  - Controles tipo Flatpickr: campo de texto con clase `flatpickr-input` y `data-enable-time`
  - Para "Semanal": checkboxes de día (Lun-Mar-Mié-Jue-Vie-Sáb-Dom)
  - Para "Personalizado": input de expresión cron
  - Botón "➕ Agregar Tarea"
- Sección "📋 Tareas Activas":
  - Tabla: Scraper | Cron | Próxima ejecución | Última ejecución | Estado | Acciones
  - Estado: badge verde "Activa" / badge gris "Pausada"
  - Acciones: ⏸️ Pausar / ▶️ Reanudar / ⏳ Ejecutar ahora / 🗑️ Eliminar

**Panel lateral de validación (en tab "Extracción"):**
- `<div class="validation-panel" id="validation-panel">` — al lado del console-section
- Cuando hay validation errors, se muestra con transición
- Cabecera: "🧪 Validación — N errores"
- Lista de items: cada uno con número de fila, campo, valor actual, input de corrección, botones "✅" / "❌"
- Badge en cabecera de scraper con contador animado

**Botón "🔍 Diagnosticar"** en cada scraper card (todos los scrapers). Modal de diagnóstico con:
- Mini tabs: "📐 Estructura" | "🔄 Cambios" | "📜 Historial"
- Árbol colapsable de selectores en "Estructura"
- Tabla de diff en "Cambios" con severity colors
- Timeline de snapshots en "Historial"

**CDN Flatpickr** agregado en `<head>`:
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css">
<script src="https://cdn.jsdelivr.net/npm/flatpickr"></script>
```

### 7. `scrapycoco/script.js`

**Scheduler CRUD:**
- `loadSchedules()` — GET `/api/scheduler/list` → renderiza tabla de tareas
- `window.addSchedule()` — lee formulario, POST `/api/scheduler/add`
- `window.pauseSchedule(id)` / `window.resumeSchedule(id)` / `window.deleteSchedule(id)`
- `window.runScheduleNow(id)` — POST `/api/scheduler/{id}/run-now`
- Inicialización de Flatpickr en el input de fecha/hora con `enableTime: true`
- Preview de próxima ejecución humana (ej. "Próxima: Lun 14 Jul 2026, 08:00")

**Validation Panel:**
- Nuevo handler SSE para evento `validation-error`
- `validationErrors: []` — acumulador global
- Al recibir validation-error:
  - Agrega a `validationErrors`
  - Actualiza contador badge
  - Renderiza/actualiza panel lateral
  - Si panel oculto, lo muestra con animación
- `window.applySuggestion(rowIndex)` — reemplaza valor con sugerencia
- `window.dismissValidation(rowIndex)` — descarta el error
- `window.applyAllSuggestions()` — aplica todas las sugerencias de una
- `window.dismissAll()` — descarta todos
- Al abrir preview modal, si hay errors, pre-filtra las filas conflictivas

**Diagnóstico:**
- `window.runDiagnostic(scraperId)` — POST `/api/diagnostic/run/{id}` → abre modal
- `renderStructureTree(snapshot)` — renderiza árbol colapsable de selectores
- `renderDiff(diff)` — tabla de cambios con severity colors
- `loadDiagnosticHistory(scraperId)` — fetch GET `/api/diagnostic/history/{id}` → timeline
- Mini tabs dentro del modal: estructura / cambios / historial

### 8. `scrapycoco/style.css`

**Validation Panel (~100 líneas):**
- `.validation-panel` — panel lateral, 320px width, border-left, slide-in animation
- `.validation-panel.visible` — `transform: translateX(0)`
- `.validation-item` — tarjeta por error, border-left rojo/ámbar
- `.validation-correction-input` — input inline pequeño
- `.validation-badge` — badge circular animado (contador)
- `.grid-with-validation` — grid layout alternativo cuando panel visible (restringe console a `1fr`)

**Scheduler (~80 líneas):**
- `.scheduler-layout` — grid de 2 columnas (formulario + lista)
- `.scheduler-table` — tabla de tareas
- `.scheduler-cron-builder` — layout de selects en grid
- `.scheduler-status` — badges verde/gris
- `.flatpickr-input` — override de dark theme para Flatpickr

**Diagnóstico (~60 líneas):**
- `.diagnostic-tree` — ul/li colapsable con toggle
- `.diagnostic-tree-toggle` — ▶/▼ indicator
- `.diff-added` — background verde tenue
- `.diff-removed` — background rojo tenue
- `.diff-changed` — background ámbar tenue
- `.diagnostic-tabs` — mini tabs dentro del modal

---

## 📐 Layouts

### Tab "Extracción" con panel de validación visible
```
┌─────────────────────────────────────────────────────────┐
│ [⚡ Extracción] [📊 Historial] [⏰ Programador] [⚙️ Config] │
├──────────────────────────────┬──────────────────────────┤
│  Scrapers Grid               │ Console Logs             │
│  ┌─────┐ ┌─────┐            │ ┌────────────────────────┐│
│  │  xG │ │cards│            │ │ [Info] [Warning] [Error]││
│  │ ☑ 🔍│ │ ☑ 🔍│           │ │                        ││
│  └─────┘ └─────┘            │ │                        ││
│  [▶️ Ejecutar Seleccionados] │ │                        ││
├──────────────────────────────┤ ├────────────────────────┤│
│  Validation Panel (320px)    │ │                        ││
│  ┌─────────────────────────┐ │ │                        ││
│  │ 🧪 Validación — 3 errors│ │ │                        ││
│  │ ┌─────────────────────┐ │ │ │                        ││
│  │ │ #42 home_score = -1 │ │ │ │                        ││
│  │ │ [ 0 ] [✅][❌]      │ │ │ │                        ││
│  │ └─────────────────────┘ │ │ └────────────────────────┘│
│  │ [✅ Aplicar todas] [❌] │ │                           │
│  └─────────────────────────┘ └──────────────────────────┘
```

### Modal de Diagnóstico
```
┌────────────────────────────────────────────────────────┐
│ 🔍 Diagnóstico: flashscore                    [✕]       │
├────────────────────────────────────────────────────────┤
│ [📐 Estructura] [🔄 Cambios] [📜 Historial]            │
├────────────────────────────────────────────────────────┤
│ ▶ div[class*=wcl-row_]          (encontrado: 12)       │
│   └── hash actual: wcl-row_c4lkc                       │
│   └── hash previo: wcl-row_c4lkc  🟢 sin cambios       │
│ ▶ div[class*=lineupsContent]    (encontrado: 1)        │
│ ▶ button[class*=tab]            (encontrado: 5)        │
│   └── labels: Estadísticas, Alineaciones, Jugadores... │
├────────────────────────────────────────────────────────┤
│ 🟢 Sin cambios estructurales detectados.               │
└────────────────────────────────────────────────────────┘
```

---

## 📦 Dependencias
- `apscheduler` — pip install apscheduler
- Flatpickr (CDN) — ya incluido vía `<link>` + `<script>` en index.html

---

## 📋 Orden de Implementación Sugerido

1. **`diagnostic.py`** + tabla `structure_snapshots` en `db.py` + `BaseScraper.run_diagnostic()` — independiente del resto
2. **`scheduler.py`** + endpoints scheduler en `main.py` — independiente
3. **Validación inline** en `BaseScraper.validate_and_report()` + SSE `validation-error` + panel lateral en frontend
4. **Frontend scheduler**: Flatpickr init, formulario, tabla de tareas, CRUD
5. **Frontend diagnóstico**: botón en cards, modal con tabs, árbol/diff/historial
6. **Integración final**: validation panel conectado a preview modal, scheduler ejecutando scrapers reales
