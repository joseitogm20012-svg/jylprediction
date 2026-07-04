# Fase 2 — Dashboard + Preview + Export

## Overview
Implements batch execution, data preview with validation, and flexible export (CSV/JSON/Excel).

## New Files

### 1. `scrapycoco/validation.py`
- `PreviewResult(columns, rows, total, warnings)` — Pydantic model
- `PreviewWarning(row, field, message, severity)` — individual warning
- `VALIDATION_RULES` — dict per scraper_id with `(field, check_fn, message)` tuples
- `validate_rows(scraper_id, rows)` → PreviewResult
  - Checks: nulls, negative values, invalid dates, empty strings, duplicates, out-of-range values

### 2. `scrapycoco/export.py`
- `export_to_csv(data, path)` → int count
- `export_to_json(data, path)` → int count
- `export_to_excel(data, path, sheet_name)` → int count (openpyxl, styled header)
- `export_data(data, format, path?, sheet_name?)` → (count, bytes?) — bytes for in-memory

### 3. `scrapycoco/transform.py`
- `to_iso_dates(rows, columns)` — tries 8 date formats → ISO 8601
- `unify_country_names(rows, column)` — maps 30+ aliases to standard names
- `drop_empty_columns(rows)` — removes all-null/empty columns
- `normalize_team_names(rows, column)` — removes accents/extra spaces, title-case
- `apply_transforms(rows, transforms[])` — orchestrates by transform IDs

## Modified Files

### 4. `scrapycoco/scrapers/base.py`
- Add `self.preview_mode = False` in `__init__`
- Add `set_preview_mode()` method
- Add `get_preview_data()` → returns `list[dict]` (to be overridden by scrapers)

### 5. `scrapycoco/main.py` — New Endpoints
- `POST /api/batch/run` — body: `{scraper_ids: string[], sandbox: bool}`
  - Sequential SSE with events: `batch-start`, `batch-progress`, log, `batch-end`
- `GET /api/preview/{scraper_id}?limit=50&sandbox=true`
  - Executes scraper in preview mode, runs `validate_rows()`, returns PreviewResult JSON
- `POST /api/export` — body: `{scraper_id, format, transforms[], preview_data?}`
  - If preview_data present → apply transforms → export that
  - Else → run scraper → validate → apply transforms → export
  - Returns FileResponse with proper Content-Disposition

### 6. `scrapycoco/index.html`
- Each scraper card: `<input type="checkbox" class="scraper-checkbox">` prepended
- Section header: batch button "▶️ Ejecutar Seleccionados" + count badge
- Batch progress bar: `<div class="batch-progress" id="batch-progress" style="display:none">`
  - Bar fill + text "2/5 completados — Scraper Actual"
- Preview modal: `<div class="modal-overlay" id="preview-modal" style="display:none">`
  - Table with sortable columns, highlighted warnings
  - Action buttons: "Guardar CSV", "Exportar como...", "Descartar"
- Config tab: new section "Exportación"
  - Format radio (CSV/JSON/Excel)
  - Transform toggles (ISO dates, unify countries, normalize teams, drop empty)
  - "Ruta por defecto" input

### 7. `scrapycoco/script.js`
- Checkbox management: toggle batch button state
- Batch run: new EventSource to `/api/batch/run` (POST, body as JSON)
  - Handle `batch-start`, `batch-progress`, `batch-end` events
  - Show/hide progress bar, update counters
- Preview:
  - Click "Vista Previa" → fetch `/api/preview/{id}` → open modal
  - Render table, highlight warning rows in red/amber
  - "Guardar" → POST to save CSV
  - "Exportar como..." → sub-modal with format picker + transforms → POST `/api/export`
- Export config:
  - Load/save defaults from localStorage
  - Build export payload from preview data

### 8. `scrapycoco/style.css`
- `.scraper-checkbox` — custom checkbox overlay on card
- `.batch-progress` — fixed bar at top, gradient fill animation
- `.modal-overlay` — dark overlay + centered modal card
- `.preview-table` — striped, sortable, with warning highlights
- `.preview-warning-row`, `.preview-error-row` — red/amber backgrounds
- `.export-config` — toggle switches, radio group, form layout

## Flow Diagrams

### Batch Execution
```
User checks cards → clicks "Ejecutar Seleccionados"
  → POST /api/batch/run {ids: ["results", "xg"], sandbox: false}
  → Server starts scraper #1
  → SSE: batch-progress {completed: 0, total: 2, current: "results"}
  → SSE: log [... individual scraper logs ...]
  → Scraper #1 done
  → SSE: batch-progress {completed: 1, total: 2, current: "xg"}
  → SSE: log [...]
  → Scraper #2 done
  → SSE: batch-end {completed: 2, failed: 0, total: 2}
```

### Preview + Export
```
User clicks "Vista Previa"
  → GET /api/preview/results?limit=50
  → Server runs validate_rows()
  → Returns PreviewResult JSON
  → Modal renders table + warnings
  → User verifies data
  → Clicks "Exportar como..."
  → Sub-modal: pick format + transforms
  → POST /api/export {scraper_id, format:"xlsx", transforms:["iso_dates","normalize_teams"], preview_data:[...]}
  → Server applies transforms, generates file
  → Browser downloads file
```

## Dependencies
- `openpyxl` — required for Excel export

## Testing
1. Check batch execution with 2-3 scrapers selected
2. Verify progress bar updates correctly
3. Open preview modal, verify warnings highlight
4. Export to CSV/JSON/Excel, verify file contents
5. Apply transforms, verify ISO dates + country unification
