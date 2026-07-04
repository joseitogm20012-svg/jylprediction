# Especificación: Squad Data, Corners, Rate Limiter y Referee Stats

Fecha: 2026-07-02
Proyecto: JLY Predictor — Mundial 2026

## 1. Resumen

Integración de datos reales de Transfermarkt y córners al modelo de predicción,
implementación de rate limiter por dominio para scrapers, y soporte básico de
estadísticas de árbitros en la UI.

### 1.1 Tareas incluidas

| # | Tarea | Estado previo | Archivos a modificar |
|---|-------|--------------|---------------------|
| 1 | Mostrar info de Transfermarkt como contexto visual | ✅ COMPLETADA | main.py, index.html, index.css, app.js |
| 2 | Integrar corners_stats.json al predictor | PENDIENTE | predictor.py |
| 3 | Rate limiter por dominio | PENDIENTE | scrapycoco/rate_limiter.py (nuevo) |
| 4 | Referee stats (simplificado) | PENDIENTE | predictor.py, app.js, index.html, index.css |

### 1.2 Tareas excluidas

| Tarea | Motivo |
|-------|--------|
| Consumir injuries.json | TM no tiene datos de lesiones para selecciones |
| Auto-sync a Supabase | Pospuesto para mejor diseño |
| Adaptar FlashScore 5 ligas + UCL | Omitido por instrucción |

---

## 2. Task 1: Info de Transfermarkt ✅ COMPLETADA

El endpoint `/api/teams` ahora devuelve `{ratings, transfermarkt}` con datos de
49 selecciones. El frontend muestra badges con valor de mercado, edad promedio
y director técnico en el encabezado VS.

**Archivos:**
- `backend/main.py` — carga `transfermarkt_stats.json` en `/api/teams`
- `frontend/index.html` — badges `.badge-tmval`, `.badge-tmage`, `.badge-tmmgr`
- `frontend/index.css` — estilos de badges con colores verde, amarillo, púrpura
- `frontend/app.js` — variable global `transfermarktData`, actualización en `updateMatchCard()`

---

## 3. Task 2: Integrar corners_stats.json

### 3.1 Problema actual

El predictor calcula córners esperados usando estimaciones desde tiros, centros
y bloqueos (líneas 1322-1442 de predictor.py). El ajuste rival usa un multiplicador
de 0.5x a 1.8x, lo que produce oscilaciones irreales (ej: Suiza contra Argelia da
~9.5 córners, contra Argentina da ~5.3).

Existe `data/corners_stats.json` con datos reales de 92 equipos (corners_for,
corners_against, games) que no se está utilizando.

### 3.2 Solución

#### 3.2.1 Carga de datos

En `predictor.py`, agregar función `load_corners_data()` que lea
`data/corners_stats.json` y devuelva un dict `{team_slug: {corners_for, corners_against}}`.
No necesita mapeo: el predictor recibe slugs desde el frontend (`team_a`, `team_b`)
y `corners_stats.json` también usa slugs como clave.

#### 3.2.2 Cambio en el cálculo de córners

Reemplazar la estimación actual de lambda base (líneas 1395-1409) por:

1. **Base real**: `corners_stats[slug_a]["corners_for"]` si existe
2. **Fallback**: si no hay datos en el JSON, usar la estimación actual
3. **Ajuste rival amortiguado**: factor de concesión limitado a ±15% (`[0.85, 1.15]`)
   en vez del rango actual `[0.5, 1.8]`
4. **Límites**: mantener clamp `[1.5, 9.5]` existente

#### 3.2.3 Fórmula final

```
lambda_a = corner_base_a * clamp(concession_factor_b, 0.85, 1.15)
lambda_b = corner_base_b * clamp(concession_factor_a, 0.85, 1.15)
```

Donde `corner_base_a` viene del JSON si existe, o de la fórmula anterior si no.

#### 3.2.4 Archivos modificados

- `backend/predictor.py` — agregar `load_corners_data()`, modificar bloque de corners

---

## 4. Task 3: Rate Limiter por Dominio

### 4.1 Problema actual

Los scrapers Playwright usan `asyncio.sleep(2)` y `asyncio.sleep(3)` dispersos
en el código. Todos los dominios se tratan igual: si un sitio responde rápido,
el scraper igual espera el delay máximo del más lento. No hay una capa central
que registre "última request a dominio X".

### 4.2 Solución

Crear `scrapycoco/rate_limiter.py` con una clase `RateLimiter`:

```python
class RateLimiter:
    def __init__(self, defaults: dict = None):
        # defaults = {"transfermarkt.com": 2.5, "flashscore.com": 1.0}
        self._domains: dict[str, float] = {}  # dominio -> último timestamp
        self._delays: dict[str, float] = defaults or {}

    def set_delay(self, domain: str, seconds: float):
        self._delays[domain] = seconds

    async def wait(self, domain: str):
        """Espera el tiempo necesario desde la última request a este dominio."""
        now = time.time()
        last = self._domains.get(domain, 0)
        elapsed = now - last
        needed = self._delays.get(domain, 1.0)
        if elapsed < needed:
            await asyncio.sleep(needed - elapsed)
        self._domains[domain] = time.time()
```

### 4.3 Comportamiento

- Instancia global en los scrapers que usan Playwright
- Cada scraper registra el dominio antes de cada request
- Si se hacen requests a diferentes dominios en secuencia, **no hay espera** (cada
  dominio tiene su propio temporizador)
- Default global de 1.0s si no hay delay específico para un dominio

### 4.4 Archivos creados/modificados

- `scrapycoco/__init__.py` — puede quedar vacío o con import
- `scrapycoco/rate_limiter.py` — NUEVO
- `scrapycoco/scrape_injuries_v5.py` — reemplazar `asyncio.sleep(2-3)` por `rate_limiter.wait("transfermarkt.com")`

---

## 5. Task 4: Referee Stats (simplificado)

### 5.1 Problema actual

El predictor modela tarjetas estadísticamente (líneas 1683-1714 de predictor.py)
basado en promedios por equipo desde FBref. El nombre del árbitro se scrapea
pero no se usa. No hay ajuste por árbitro en la proyección de tarjetas.

### 5.2 Solución (simplificada)

#### 5.2.1 Modelo de tarjetas

Agregar un multiplicador de "intensidad del árbitro" configurable desde el
frontend:

```
expected_cards *= referee_intensity
```

Donde `referee_intensity` es un slider que va de 0.5x ("Permisivo") a 1.5x
("Estricto"), default 1.0x ("Promedio").

#### 5.2.2 Endpoint / predict

Agregar campo opcional `refereeIntensity: float` al `PredictionRequest`.

#### 5.2.3 Frontend

- Slider en el panel de parámetros: "Intensidad del árbitro" con etiquetas
  "Permisivo ← → Estricto"
- Si en el futuro se scrapean perfiles reales, este slider se reemplaza por
  un selector de árbitro — la UI ya está preparada

#### 5.2.4 Archivos modificados

- `backend/main.py` — agregar `refereeIntensity` al modelo
- `backend/predictor.py` — aplicar multiplicador en bloque de tarjetas
- `frontend/index.html` — slider en panel de parámetros
- `frontend/index.css` — estilos del slider
- `frontend/app.js` — enviar `refereeIntensity` en request, actualizar UI

---

## 6. No incluido (decisiones explícitas)

- **Lesiones**: no hay fuente viable para selecciones nacionales (TM 404)
- **Sync Supabase**: se diseñará por separado cuando haya un esquema claro
- **FlashScore 5 ligas + UCL**: omitido por instrucción
- **Referee stats avanzado** (scrapeo de perfiles): se pospone para después
  del MVP de esta tarea

---

## 7. Riesgos y mitigaciones

| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| El slug del equipo no existe en corners_stats.json | Baja | Fallback a fórmula actual si no hay match |
| Rate limiter en Playwright no captura bien las URLs | Media | Usar `page.url` antes de cada navegación como dominio |
| Slider de referee no mejora las predicciones reales | Alta | Es feature de UX, no se espera impacto medible hasta tener datos reales |
