# AGENTS.md — Contexto del Proyecto JLY Predictor

Este archivo está diseñado para que cualquier agente de IA (como Cline, Copilot, GPT, etc.) pueda entender el contexto completo del proyecto al leerlo. Documenta la arquitectura, lógica de funcionamiento, historial de ediciones y convenciones del proyecto.

---

## 📋 Descripción General

**JLY Predictor** es un simulador estadístico de partidos del **Mundial 2026**. Combina un modelo Elo calibrado, regresión Poisson bivariada Dixon-Coles, simulación Monte Carlo y ajustes contextuales (altitud, sede anfitriona, overrides) para predecir resultados de fútbol de selecciones.

Incluye: simulador de partidos, cuentas de usuario con Supabase Auth, leaderboard comunitario, panel de administración, análisis tácticos IA y backtesting del modelo.

---

## 🧱 Stack Técnico

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.12+ / FastAPI / Uvicorn |
| Frontend | HTML5 + CSS3 + JavaScript vanilla |
| Charts | Chart.js (CDN) |
| UI Components | Tom Select (dropdowns búsqueda) |
| DB desarrollo | SQLite (`data/user_data.db`) |
| DB producción | PostgreSQL (Supabase) |
| Auth | Supabase Auth (JWT) |
| Hosting | Render (Web Service) |
| CLI legacy | Node.js 18+ (`.mjs`) |
| Motor numérico | NumPy, Numba (predictor.py) |

---

## 📁 Estructura del Proyecto

```
/
├── main.py                 # API FastAPI (endpoints REST + static files)
├── predictor.py            # Motor estadístico (Elo, Poisson, Monte Carlo)
├── db.py                   # Capa de datos (SQLite/Postgres + CRUDs)
├── app.js                  # Lógica frontend del simulador
├── index.html              # Página principal
├── index.css               # Estilos (tema oscuro/claro)
├── admin.html              # Panel de administración
├── admin.js                # Lógica del panel admin
│
├── data/
│   ├── results.csv         # Resultados históricos de partidos
│   ├── elo-calibrated.json # Ratings Elo por selección
│   ├── xg_by_team.json     # xG, tiros, centros por equipo (FBref)
│   ├── ai_analyses.json    # Análisis tácticos (migrado a DB)
│   ├── user_data.db        # SQLite con usuarios, favoritos, pronósticos
│   ├── goalscorers.csv     # Goleadores históricos
│   ├── corners_stats.json  # Estadísticas de corners
│   ├── model-backtest.json # Resultados de backtesting
│   ├── logged_predictions.json # Predicciones guardadas
│   ├── fetch_fbref_xg.py   # Script: descarga xG de FBref
│   ├── fetch_latest_results.py # Script: actualiza resultados
│   ├── fetch_wc2026_missing.py # Script: datos faltantes WC2026
│   ├── download_international_data.py # Script: datos internacionales
│   └── generate_elo_ratings.py # Script: genera ratings Elo
│
├── backtesting/
│   ├── backtest.py         # Backtesting del modelo (Python)
│   └── backtest_results.json
│
├── scratch/                # Scripts auxiliares de análisis/limpieza
│   ├── find_leftover_emojis.py
│   ├── verify_dom_ids.py
│   ├── replace_flags.py
│   └── ... (otros scripts de depuración)
│
├── elo.mjs                 # CLI: cálculo Elo (Node, legado)
├── calibrate.mjs           # CLI: calibrar Elo desde results.csv
├── backtest.mjs            # CLI: backtesting (Node, legado)
├── predict.mjs             # CLI: predicción head-to-head
├── track-record.mjs        # CLI: seguimiento de aciertos
├── tournament_sim.py       # Simulación de torneo completo
│
├── test_crud.py            # Tests de CRUD análisis IA
├── test_user_features.py   # Tests de funcionalidades de usuario
├── test_changes.py         # Tests de cambios
├── test_soccerdata.py      # Tests de datos de fútbol
│
├── requirements.txt        # Dependencias Python
├── package.json            # Dependencias Node (solo CLI)
├── .env / .env.example     # Variables de entorno
├── run.bat                 # Script de arranque Windows
├── update_xg.bat           # Script actualizar xG
├── update_results.bat      # Script actualizar resultados
└── AGENTS.md               # ← Este archivo
```

---

## 🔄 Flujo de Funcionamiento

```
Usuario abre index.html
  → app.js inicializa: carga ratings, popula dropdowns
  → Usuario selecciona Equipo A, Equipo B + parámetros
  → app.js llama POST /api/predict
    → main.py recibe request
    → predictor.py:
        1. load_data() → carga results.csv + elo-calibrated.json
        2. load_xg_data() → carga xG real de FBref
        3. compute_xg_from_raw_data() → calcula xG esperados
           - Forma reciente ponderada (decay exponencial)
           - Ranking FIFA + Elo
           - Historial H2H
           - Ajuste por altitud (>1500m)
           - Bono sede anfitriona WC 2026 (CONCACAF)
           - Strength overrides manuales
        4. Distribución Poisson bivariada (Dixon-Coles τ = -0.13)
        5. Monte Carlo vectorizado (NumPy, hasta 100K sims)
        6. Calcula mercados: 1X2, BTTS, O/U, Hándicaps, Córners
      ← Devuelve JSON con resultados
  → app.js renderiza: probabilidades, marcadores, gráficos, heatmap
```

---

## 🧠 Modelo Estadístico (predictor.py)

### 1. Cálculo de xG (Expected Goals)

El xG de cada equipo es un promedio ponderado de 3 componentes:

- **Forma (w_form)**: `gs_a * gc_b` donde `gs/gc` son goles a favor/en contra ponderados por calidad del rival y decay exponencial (half-life configurable). Se mezcla con xG real de FBref si está disponible (blend 60-70%).
- **Ranking (w_fifa)**: Combina diferencia de rating Elo y diferencia de ranking FIFA.
- **H2H (w_h2h)**: Basado en diferencia de goles promedio en enfrentamientos directos.

**Reglas de Oro:**
- Si no hay H2H en CSV → `h2h_weight = 0%`
- Si un equipo tiene <5 partidos recientes → `fifa_weight` mínimo 55%
- Los pesos se normalizan para que sumen 1.0

### 2. Ajustes Contextuales

- **Altitud**: Si >1500msnm, penalización 8% por cada 1000m adicionales (máx 30%). Equipos aclimatados (MEX, ECU, COL, BOL) exentos.
- **Sede WC 2026**: Equipos CONCACAF reciben bono jugando en su país anfitrión (USA +8%, CAN/MEX +3%, resto CONCACAF +3%).
- **Strength Override**: Multiplicador manual de fuerza (0.5x - 2.0x).

### 3. Dixon-Coles

Matriz de probabilidades conjuntas usando Poisson bivariada con corrección τ (rho = -0.13) para los resultados 0-0, 0-1, 1-0, 1-1. Se estima dinámicamente desde datos históricos si hay suficientes muestras.

### 4. Monte Carlo

Simulación vectorizada con NumPy: se generan N números aleatorios, se mapean a la CDF de la matriz conjunta, y se cuentan frecuencias de cada marcador.

### 5. Mercados calculados

- 1X2 (Local/Empate/Visitante)
- Top 5 marcadores más probables
- BTTS (Both Teams To Score)
- Over/Under (0.5, 1.5, 2.5, 3.5)
- Doble Oportunidad (1X, 12, X2)
- Draw No Bet
- Hándicaps Asiáticos (-1.5, -0.5, +0.5, +1.5)
- Córners esperados
- Valor esperado (EV) vs cuotas de mercado
- Heatmap 5x5 de resultados
- Gráfico radar comparativo

---

## 🗄️ Base de Datos (db.py)

**Modo dual**: SQLite (`data/user_data.db`) en desarrollo, PostgreSQL en producción.

Tablas:
| Tabla | Propósito |
|-------|-----------|
| `favorites` | Predicciones guardadas por usuario |
| `user_presets` | Configuraciones personalizadas de parámetros |
| `match_votes` | Encuestas comunitarias (votación 1X2) |
| `user_pronostics` | Pronósticos oficiales para leaderboard |
| `leaderboard` | Ranking de usuarios (puntos) |
| `ai_analyses` | Análisis tácticos IA por partido |

**Auth**: Supabase Auth (JWT). El backend verifica tokens contra `SUPABASE_URL/auth/v1/user`.

---

## 👤 Funcionalidades de Usuario

- **Registro/Login**: vía Supabase Auth (email, Google, etc.)
- **Favoritos**: guardar predicción con todos los detalles
- **Presets**: configuraciones reutilizables (pesos, decay, overrides)
- **Votación**: polls comunitarios 1X2 por partido
- **Pronósticos**: predicción oficial (1 por partido), compite en leaderboard
  - Acierto: +10 pts
  - Se resuelven automáticamente cuando hay resultado real
- **Planes**: FREE / PREMIUM (vía metadata de Supabase)
- **Leaderboard**: top 100 usuarios por puntos

---

## 🔧 API Endpoints (main.py)

### Públicos
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/config` | Config pública de Supabase |
| GET | `/api/teams` | Lista de equipos con ratings |
| POST | `/api/predict` | Simular partido |
| POST | `/api/betbuilder/simulate` | Simular bet builder |
| GET | `/api/history/{team}` | Historial de un equipo |
| GET | `/api/history/advanced/{a}/{b}` | H2H avanzado |
| GET | `/api/h2h/{a}/{b}` | Estadísticas H2H |
| GET | `/api/backtest-metrics` | Resultados de backtest |
| POST | `/api/log-prediction` | Guardar predicción |
| GET | `/api/logged-predictions` | Listar predicciones guardadas |
| POST | `/api/resolve-prediction` | Resolver predicción manual |
| POST | `/api/update-prediction-results` | Auto-resolver con resultados reales |
| GET | `/api/ai-analyses` | Todos los análisis IA |
| GET | `/api/ai-analyses/{a}/{b}` | Análisis IA para un partido |
| POST | `/api/lookup-username` | Buscar email por username |
| POST | `/api/run-backtest` | Ejecutar backtest (Node) |

### Requieren Auth (Supabase JWT)
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/user/favorites` | Añadir favorito |
| GET | `/api/user/favorites` | Listar favoritos |
| DELETE | `/api/user/favorites/{id}` | Eliminar favorito |
| POST | `/api/user/presets` | Guardar preset |
| GET | `/api/user/presets` | Listar presets |
| DELETE | `/api/user/presets/{id}` | Eliminar preset |
| POST | `/api/match/vote` | Votar partido |
| GET | `/api/match/vote/{a}/{b}` | Ver votos |
| POST | `/api/match/pronostic` | Registrar pronóstico |
| GET | `/api/match/pronostic/{a}/{b}` | Ver pronóstico |
| GET | `/api/leaderboard` | Ranking global |

### Requieren ADMIN_PASSWORD
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/ai-auth/verify` | Verificar contraseña admin |
| POST | `/api/ai-analyses` | Crear/editar análisis IA |
| DELETE | `/api/ai-analyses/{id}` | Eliminar análisis IA |
| GET | `/api/admin/users` | Listar usuarios |
| PUT | `/api/admin/users/{id}/plan` | Cambiar plan de usuario |

---

## 📜 Historial de Commits (cambios recientes)

Últimos cambios en orden cronológico (del más reciente al más antiguo):

| Commit | Fecha | Descripción |
|--------|-------|-------------|
| `1cd6510` | 2026-06-26 | **Migrar análisis IA a DB + admin**: Se movieron los análisis tácticos de JSON a base de datos SQLite/Postgres. Se creó `db.py` con CRUD completo. Se implementó `admin.html`/`admin.js` para gestión de usuarios (FREE/PREMIUM) y análisis IA. Se añadieron `test_crud.py` y `test_user_features.py`. |
| `21f8b66` | 2026-06-21 | **Tabla Hándicaps Asiáticos 8 filas**: Implementación completa de tabla de hándicaps asiáticos con líneas positivas y negativas para ambos equipos, placeholders dinámicos en sidebar y soporte multi-span para actualización de EV. |
| `84d427e` | 2026-06-21 | **Columnas Sí/No en Hándicaps**: La tabla de hándicaps asiáticos ahora muestra columnas separadas "Sí" (acierta) y "No" (falla) para cada línea de hándicap. |
| `0ff0182` | 2026-06-21 | **Layout simplificado Hándicaps**: Formato `TeamName: Percentage` dentro de las celdas de hándicap asiático. |
| `d68bf0a` | 2026-06-21 | **Badges de hándicap**: Se añadieron badges explícitos (+/- línea) para cada equipo en cada celda de la tabla. |
| `ea3df23` | 2026-06-21 | **Fix theme toggle + Chart.js**: Corrección del botón de cambio de tema (pointer-events en SVGs), adaptación dinámica de configuraciones de Chart.js al iniciar. |
| `685bef3` | 2026-06-21 | **Heatmap + barras + radar**: Implementación de matriz de calor 5x5 de resultados, barras comparativas lado a lado, gráfico radar hexagonal y panel de guía de parámetros. |
| `33e34f6` | 2026-06-21 | **Fix DOM + gauges + tabs**: Corrección de discrepancias de elementos DOM, renderizado de gauges circulares y cambio de pestañas en `app.js`. |
| `2822af8` | 2026-06-21 | **Fix variable global duplicada**: Se eliminó declaración duplicada de variable global en `app.js` y se limpió el repositorio Git. |
| `ef913c0` | 2026-06-21 | **Optimización layout + mobile + H2H + Render**: Mejoras de layout, scroll en móvil, orden de H2H y binding de puerto en Render. |

---

## 🎨 Convenciones de Código

### Generales
- **Idioma**: Comentarios y UI en español; código (variables, funciones) en inglés
- **Sin comentarios triviales**: No añadir comentarios a menos que sean necesarios para entender lógica compleja
- **Responsabilidad única**: Funciones pequeñas y enfocadas (ver `compute_xg_from_raw_data` vs `load_match_raw_data`)
- **Cache**: Uso de `lru_cache` y cachés manuales (`_cached_xg_data`, `_cached_matches`, `BET_BUILDER_CACHE`)
- **Errores**: Todas las funciones retornan valores seguros (fallbacks) en lugar de lanzar excepciones no controladas

### Frontend (JavaScript)
- **ES module**: No usado en frontend (JS vanilla global); los archivos `.mjs` son Node.js
- **DOM**: Los modales se crean dinámicamente con `innerHTML` + `uuid` basado en timestamp
- **Tema**: El tema oscuro/claro se guarda en `localStorage('theme')`; se aplica antes del render para evitar flash
- **Eventos**: Se usa `onclick` en HTML para funciones globales (ej. `window.viewTeamDetails`)
- **Fetch**: Llamadas a API con `async/await` y manejo de errores silencioso

### Backend (Python)
- **FastAPI**: Modelos Pydantic para requests/responses; `HTTPException` para errores
- **SQLite/Postgres**: Capa de abstracción en `db.py` con `execute_sql()` que traduce automáticamente entre SQLite (`?`) y Postgres (`%s`), y entre `INSERT OR REPLACE` y `ON CONFLICT DO UPDATE`
- **Static files**: Se montan al final para no enmascarar rutas API
- **CORS**: Abierto (`*`) para desarrollo local

### Modelo Estadístico
- **xG**: Clampeado entre 0.1 y 4.5 goles esperados
- **Poisson**: Tabla de hasta 10 goles por equipo (matriz 11x11)
- **Rho**: Estimado desde datos históricos, suavizado al valor teórico (-0.13), clamped a [-0.5, 0.5]
- **NumPy**: Monte Carlo con `np.random.rand` + `np.searchsorted` + `np.unique`

---

## 🔐 Variables de Entorno (.env)

| Variable | Requerida | Uso |
|----------|-----------|-----|
| `ADMIN_PASSWORD` | Sí (admin) | Contraseña panel `/admin.html` |
| `SUPABASE_URL` | Sí | URL del proyecto Supabase |
| `SUPABASE_PUBLISHABLE_KEY` | Sí | Anon key (expuesta al frontend) |
| `SUPABASE_SECRET_KEY` | Sí (admin) | Service role (solo backend) |
| `DATABASE_URL` | Sí (prod) | Postgres connection string |
| `PORT` | Auto (Render) | Puerto servidor (default 3000) |

---

## 🚀 Inicio Rápido

```bash
pip install -r requirements.txt
cp .env.example .env
# Editar .env con credenciales de Supabase
python main.py
# Abrir http://localhost:3000
```

---

## ⚠️ Notas para la IA

Al editar este proyecto, tener en cuenta:

1. **predictor.py** es el archivo más crítico y sensible — cualquier cambio en el modelo afecta todas las predicciones
2. **db.py** maneja dos dialectos SQL — probar siempre ambos modos si se añaden/queries
3. **app.js** tiene ~4500 líneas — la mayoría de la lógica frontend está aquí, incluyendo modales dinámicos
4. **No usar emojis en código nuevo** — el proyecto usa emojis en UI pero no en identificadores
5. **Los `.mjs` son legado** — la migración a Python está casi completa, pero backtest.mjs y calibrate.mjs aún se usan desde la API
6. **Los archivos en `scratch/` son herramientas de análisis** — no afectan la app principal
7. **El caché** es común en el código (LRU, dict manual) — invalidar al cambiar datos subyacentes
8. **Tema oscuro/claro** — verificar siempre ambos modos al hacer cambios visuales
9. **Mobile responsive** — la UI debe funcionar en móvil (layout adaptativo, scroll)
10. **Pruebas**: `test_crud.py` para admin, `test_user_features.py` para usuario (requieren `.env` configurado)
