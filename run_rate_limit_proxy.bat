@echo off
rem ------------------------------------------------------------
rem  run_rate_limit_proxy.bat
rem  Automates creation of a virtual environment, installs Python
rem  dependencies and starts the FastAPI rate‑limit proxy.
rem ------------------------------------------------------------

rem ==== 1. Move to the directory where this script lives ==== 
cd /d "%~dp0"

rem ==== 2. Load environment variables from .env (if exists) ==== 
if exist ".env" (
    for /f "usebackq tokens=* delims=" %%A in (".env") do (
        set "%%A"
    )
)

rem ==== 3. Enter the proxy sub‑folder ==== 
if not exist "rate_limit_proxy" (
    echo *** ERROR: No se encuentra la carpeta "rate_limit_proxy".
    pause
    exit /b 1
)
cd rate_limit_proxy

rem ==== 4. Create virtual environment if missing ==== 
if not exist ".venv" (
    echo Creando entorno virtual .venv ...
    python -m venv .venv
) else (
    echo Entorno virtual .venv ya existe, se reutiliza.
)

rem ==== 5. Activate the virtual environment ==== 
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo *** ERROR: No se pudo activar el entorno virtual.
    pause
    exit /b 1
)

rem ==== 6. Upgrade pip and install dependencies ==== 
python -m pip install --upgrade pip
pip install fastapi uvicorn httpx
if errorlevel 1 (
    echo *** ERROR: La instalacion de dependencias fallo.
    pause
    exit /b 1
)

rem ==== 7. Start the proxy (opens a new window) ==== 
start "NVIDIA‑Rate‑Limit‑Proxy" cmd /k "cd /d %cd% && uvicorn proxy:app --host 0.0.0.0 --port 8080"

rem ==== 8. Done ==== 
exit /b 0
