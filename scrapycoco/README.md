# ScrapyCoco 🥥 — Administrador Visual de Scrapers

**ScrapyCoco** es una aplicación web independiente diseñada para consolidar, ejecutar y monitorear todos los scrapers de datos estadísticas de fútbol del proyecto **JLY Predictor**.

Permite ejecutar los scripts de extracción y ver la consola de salida (`stdout` / `stderr`) en tiempo real directamente desde el navegador, asegurando un control absoluto del flujo de datos sin necesidad de interactuar con la línea de comandos.

---

## 📁 Estructura del Programa

La aplicación está contenida en la carpeta `/scrapycoco/` y está compuesta por los siguientes archivos:

* **[main.py](file:///c:/Users/Equipo/Desktop/predecirv2/scrapycoco/main.py)**: Servidor backend en FastAPI. Expone la API REST para consultar scrapers y transmite la salida de consola en tiempo real usando Server-Sent Events (SSE).
* **[index.html](file:///c:/Users/Equipo/Desktop/predecirv2/scrapycoco/index.html)**: Interfaz gráfica web. Diseñada con un tema oscuro premium (Slate-950), tarjetas interactivas de scrapers y una terminal web integrada.
* **[style.css](file:///c:/Users/Equipo/Desktop/predecirv2/scrapycoco/style.css)**: Estilos visuales de la interfaz gráfica usando variables CSS modernas, glassmorphism, responsive móvil y animaciones dinámicas.
* **[script.js](file:///c:/Users/Equipo/Desktop/predecirv2/scrapycoco/script.js)**: Controlador frontend. Se comunica con el backend mediante peticiones HTTP fetch e implementa la API de `EventSource` para capturar la transmisión de logs en tiempo real.

---

## ⚙️ Funcionamiento Técnico

### 1. Servidor Backend (`main.py`)
El servidor backend se levanta en el puerto **3006** para no interferir con la aplicación del predictor principal (puerto 3000). Expone los siguientes endpoints principales:
* `GET /api/scrapers`: Retorna la lista de scrapers disponibles, descripción, su estado actual de ejecución (`running` o `idle`), marca de tiempo de la última corrida y código de salida del último subproceso.
* `GET /api/run/{scraper_id}`: Arranca un subproceso asíncrono en Python (`asyncio.create_subprocess_exec`) para ejecutar el script correspondiente en la raíz del proyecto. Retorna una respuesta de tipo `text/event-stream` (SSE), la cual lee la salida estándar del subproceso línea por línea y la transmite en vivo al navegador.

### 2. Transmisión de Logs en Tiempo Real (`script.js`)
Cuando el usuario presiona "⚡ Ejecutar", el frontend crea una conexión persistente:
```javascript
const eventSource = new EventSource('/api/run/' + scraperId);
```
El backend transmite la consola en vivo y el frontend actualiza dinámicamente el widget de terminal web. Al finalizar el subproceso, se cierra la conexión y se refresca el estado del scraper (Éxito o Fallo).

---

## 🚀 Lista de Scrapers Soportados

La suite de extracción de ScrapyCoco gestiona los siguientes scrapers integrados:

1. **Actualizar Resultados** (`data/fetch_latest_results.py`): Descarga resultados de partidos internacionales de selecciones recientes y actualiza el archivo maestro `results.csv`.
2. **xG, Tiros y Centros (FBref - For)** (`data/fetch_fbref_xg.py`): Scrapea métricas de producción ofensiva para modelar los goles a favor.
3. **xGA (FBref - Against)** (`data/fetch_fbref_xga.py`): Scrapea métricas de solidez defensiva y goles esperados concedidos (xGA) en contra de cada selección.
4. **Tarjetas y Faltas (FBref - Misc)** (`data/fetch_fbref_cards.py`): Extrae información de disciplina (tarjetas amarillas, rojas y faltas) para el cálculo del índice de disciplina.
5. **Flashscore Match Stats (Playwright)** (`scrapers/flashscore.py`): Extrae estadísticas en tiempo real (posesión, tiros, faltas) para un partido.
6. **Transfermarkt Squad Data (Playwright)** (`scrapers/transfermarkt.py`): Extrae edad promedio, entrenador actual y valor total de la selección.
7. **Datos Faltantes Mundial 2026** (`data/fetch_wc2026_missing.py`): Completa datos de las selecciones clasificadas y estadios sede del Mundial 2026.
8. **Calcular Ratings Elo** (`data/generate_elo_ratings.py`): Ejecuta el recalibrado global de ratings Elo a partir de todo el historial en `results.csv`.
9. **Tiros por Jugador (FBref - Shooting)** (`data/fetch_fbref_shooting.py`): Scrapea estadísticas de tiros, tiros a puerta y goles por jugador.
10. **Asistencias y Pases (FBref - Standard)** (`data/fetch_fbref_passing.py`): Scrapea asistencias, goles, tarjetas y minutos por jugador.
11. **Porteros (FBref - Goalkeeping)** (`data/fetch_fbref_keepers.py`): Scrapea estadísticas de porteros: vallas invictas, atajadas, goles recibidos.
12. **Córners por Equipo (FBref - Misc)** (`data/fetch_fbref_corners.py`): Scrapea estadísticas de córners y centros por equipo.
13. **Estadísticas Avanzadas (Sofascore)** (`scrapers/sofascore.py`): Extrae datos detallados de tiros, tarjetas y asistencias desde la API de Sofascore.

---

## 🛠️ Cómo Iniciar la Interfaz

Para iniciar ScrapyCoco, ejecuta el servidor desde la terminal:

```bash
cd scrapycoco
python main.py
```

Una vez encendido, abre tu navegador web en: **[http://localhost:3006](http://localhost:3006)**.
