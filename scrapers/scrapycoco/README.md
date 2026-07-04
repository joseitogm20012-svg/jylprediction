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
El servidor backend se levanta en el puerto **3005** para no interferir con la aplicación del predictor principal (puerto 3000). Expone dos endpoints principales:
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
5. **Datos Faltantes Mundial 2026** (`data/fetch_wc2026_missing.py`): Completa datos de las selecciones clasificadas y estadios sede del Mundial 2026.
6. **Calcular Ratings Elo** (`data/generate_elo_ratings.py`): Ejecuta el recalibrado global de ratings Elo a partir de todo el historial en `results.csv`.

---

## 🛠️ Cómo Iniciar la Interfaz

Para iniciar ScrapyCoco, ejecuta el servidor desde la terminal:

```bash
cd scrapycoco
python -m uvicorn main:app --host 0.0.0.0 --port 3005 --reload
```

Una vez encendido, abre tu navegador web en: **[http://localhost:3005](http://localhost:3005)**.
