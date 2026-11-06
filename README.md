# JLY Predictor

Simulador estadístico de partidos del **Mundial 2026** con modelo transparente, comunidad de pronosticadores y panel de administración.

Combina **Elo calibrado**, **Poisson bivariado Dixon-Coles** y **simulación Monte Carlo** (hasta 100.000 iteraciones) con capas propias: xG por selección, historial directo (H2H), ranking FIFA, altitud, ventaja de sede WC 2026 y overrides manuales de fuerza.

---

## Qué incluye la plataforma

| Módulo | Descripción |
|--------|-------------|
| **Simulador** | Probabilidades 1X2, marcadores más probables, mercados de goles y análisis de valor vs cuotas |
| **Cuentas de usuario** | Registro/login con Supabase Auth, favoritos, presets personalizados, votos y pronósticos |
| **Leaderboard** | Ranking de usuarios que compiten contra el modelo durante el torneo |
| **Análisis IA** | Informes tácticos por partido, gestionados desde el panel admin |
| **Backtest** | Evaluación walk-forward reproducible con RPS, log-loss, Brier y calibración |

---

## Stack técnico

```
Frontend (HTML/CSS/JS)  →  FastAPI (Python)  →  Supabase
                              ↓
                    Postgres (producción) / SQLite (local)
```

- **Hosting:** [Render](https://render.com) — Web Service con Uvicorn  
- **Auth:** Supabase Auth (JWT)  
- **Base de datos app:** Supabase Postgres en producción (`DATABASE_URL`); SQLite local en desarrollo  
- **Motor estadístico:** Python (`predictor.py`) + scripts Node auxiliares (`backtest.mjs`, `calibrate.mjs`)

---

## Inicio rápido (local)

### Requisitos

- Python 3.10+
- Node.js 18+ (solo para backtest/calibración CLI)
- Cuenta Supabase con Auth habilitado

### 1. Clonar e instalar

```bash
git clone <tu-repo>
cd predecirv2
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales de Supabase (ver sección [Variables de entorno](#variables-de-entorno)).

### 3. Arrancar

```bash
python main.py
# o en Windows:
run.bat
```

Abre **http://localhost:3000** · Panel admin: **http://localhost:3000/admin.html**

---

## Despliegue en Render + Supabase

### Supabase (una sola vez)

1. Crea un proyecto en [supabase.com](https://supabase.com).  
2. **Settings → API:** copia `Project URL`, `anon public` key y `service_role` key.  
3. **Settings → Database → Connection string:** copia la URI del **Session pooler** (puerto 6543).  
4. En **Authentication → Providers**, habilita Email (y los que necesites).  
5. Las tablas de la app (`favorites`, `user_presets`, `match_votes`, `user_pronostics`, `leaderboard`, `ai_analyses`) se crean automáticamente al primer arranque del backend.

### Render

1. **New → Web Service** conectado a tu repositorio.  
2. **Runtime:** Python 3  
3. **Build command:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Start command:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
5. Añade las variables de entorno del [`.env.example`](./.env.example) en el dashboard de Render (nunca subas `.env` al repo).

> En producción, `DATABASE_URL` debe apuntar al Postgres de Supabase. Sin ella, Render usaría SQLite efímero y perderías datos entre redeploys.

---

## Variables de entorno

| Variable | Obligatoria | Uso |
|----------|-------------|-----|
| `ADMIN_PASSWORD` | Sí (admin) | Contraseña del panel `/admin.html` |
| `SUPABASE_URL` | Sí | URL del proyecto Supabase |
| `SUPABASE_PUBLISHABLE_KEY` | Sí | Anon key — expuesta al frontend vía `/api/config` |
| `SUPABASE_SECRET_KEY` | Sí (admin/users) | Service role — solo backend |
| `DATABASE_URL` | Sí (producción) | Connection string Postgres de Supabase |
| `PORT` | Auto en Render | Puerto del servidor (default `3000`) |

Plantilla completa: [`.env.example`](./.env.example)

---

## Cómo funciona el modelo

1. **Fuerza de equipo (Elo + xG + forma):** ratings calibrados con partidos internacionales reales, mezclados con xG por selección, ranking FIFA e historial H2H según ponderaciones del usuario.  
2. **Cada partido (Dixon-Coles):** los goles esperados alimentan una matriz Poisson bivariada con corrección τ para empates bajos (0-0, 1-1).  
3. **Monte Carlo:** se simulan N partidos virtuales para estabilizar probabilidades y mercados derivados (Over/Under, BTTS, etc.).  
4. **Ajustes contextuales:** altitud, sede anfitriona WC 2026 (USA/México/Canadá) y multiplicadores manuales por equipo.

### Scripts CLI (Node)

```bash
node predict.mjs brazil argentina      # head-to-head
node backtest.mjs                      # métricas out-of-sample
node calibrate.mjs                     # regenerar Elo desde data/results.csv
```

---

## Estructura del proyecto

| Archivo / carpeta | Rol |
|-------------------|-----|
| `main.py` | API FastAPI + archivos estáticos |
| `predictor.py` | Modelo de simulación (Python) |
| `db.py` | Capa de datos (SQLite / Postgres) |
| `app.js` / `index.html` | Frontend del simulador |
| `admin.html` / `admin.js` | Panel de administración |
| `elo.mjs` / `backtest.mjs` | Motor estadístico CLI original |
| `data/` | Resultados, Elo, xG, backtest |
| `data/fetch_*.py` | Scripts para actualizar datos |

---

## Panel de administración

Accede en `/admin.html` con la contraseña definida en `ADMIN_PASSWORD`.

Desde ahí puedes:

- Ver y gestionar **usuarios registrados** (planes FREE / PREMIUM vía Supabase Auth metadata)  
- Crear, editar y eliminar **análisis tácticos** por partido  
- Registrar cuotas de mercado opcionales junto a cada análisis  

---

## Actualizar estadísticas de córners

El scraper híbrido obtiene córners por partido de dos fuentes y los guarda en `data/per_match_corners.json`.

```bash
# Ejecutar scraper (Soccerway + FlashScore fallback)
update_corners.bat

# O directamente:
python scrapycoco\scrape_corners_hybrid.py --update

# Log de ejecución en
logs\corners_scraper.log
```

**Fuentes:**
1. **Soccerway** (primaria) — HTTP + BeautifulSoup
2. **FlashScore** (fallback) — Playwright headless Chromium

**Verificar datos:**
```bash
# Exportar datos a Excel en el escritorio
python data\export_corners_excel.py
```

**Requisitos:**
- `playwright` instalado (`playwright install chromium`)

---

## Cliente OpenAI (NVIDIA)

Cliente para el modelo `z-ai/glm-5.2` vía API de NVIDIA. Ubicado en `.opencode/openai_client.py`.

```bash
# Configurar API key
set NVIDIA_API_KEY=tu_clave   # Windows
export NVIDIA_API_KEY=tu_clave  # Linux/Mac

# Ejecutar cliente (streaming a stdout)
python .opencode\openai_client.py
```

---

## Tests

```bash
# Suite completa del scraper de córners
python -m pytest tests/scrape_corners_hybrid/ -v

# CRUD de análisis IA (requiere ADMIN_PASSWORD en .env o entorno)
set ADMIN_PASSWORD=tu_password   # Windows
export ADMIN_PASSWORD=tu_password  # Linux/Mac
python test_crud.py
```

---

## Módulo de Gestión (MVC + MongoDB)

Este módulo cumple el requisito del Proyecto 1 de **Programación III**: arquitectura MVC, base de datos NoSQL (MongoDB) y motor de plantillas Jinja2, con enrutamiento HTTP y CRUD completo desde la interfaz web.

### Qué incluye

- **Entidad:** `Equipo` (selección nacional) con `nombre`, `confederacion`, `ranking_fifa`, `rating_elo`, `escudo_url`, `notas`.
- **Validaciones:** Pydantic v2 (longitudes, rangos, URL válida, unicidad de nombre case-insensitive).
- **Arquitectura:** `backend/models/`, `backend/controllers/`, `backend/routes/`, `backend/views/` (plantillas Jinja2).
- **CRUD web:** listar, crear, ver, editar, eliminar con mensajes de éxito/error claros.
- **Manejo de errores:** 503 si Mongo no está configurado, 404 para IDs inválidos/inexistentes, 400 para datos inválidos.

### Variables de entorno (añadir a `.env`)

| Variable | Obligatoria | Uso |
|----------|-------------|-----|
| `MONGODB_URI` | Sí | URI de conexión a MongoDB Atlas (o local) |
| `MONGODB_DB` | No (default `jly_predictor`) | Nombre de la base de datos |

> **Nota para Render:** para que el módulo funcione en producción hay que crear el cluster de MongoDB Atlas (capa gratuita) y agregar `MONGODB_URI` y `MONGODB_DB` en **Render → Environment**, igual que las demás variables.

### URL del módulo

- Local: `http://localhost:3000/gestion/equipos/`
- En producción: `https://tu-app.onrender.com/gestion/equipos/`

### Cómo ejecutar los tests

```bash
python -m pytest tests/test_gestion_equipos.py -v
```

### Cómo ejecutar el seed (pobla 8 equipos de demo)

```bash
python scripts/seed_equipos.py
# Salida esperada: "8 equipos insertados"
```

---

## Créditos

El núcleo estadístico (Elo + Dixon-Coles + Poisson) se inspira en el modelo open source de [cup26matches.com](https://cup26matches.com).  
**JLY Predictor** es una capa de producto propia: UI, auth, comunidad, admin y extensiones del modelo.

Licencia: MIT — ver [LICENSE](./LICENSE).
# force rebuild
