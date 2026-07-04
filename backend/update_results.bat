@echo off
cd /d "%~dp0"

echo ============================================================
echo   Actualizando Partidos Recientes de Selecciones Nacionales
echo ============================================================
echo.

echo [1/2] Descargando resultados y mostrando ultimos partidos...
echo.
python data\fetch_latest_results.py
if errorlevel 1 (
    echo.
    echo [ADVERTENCIA] No se pudo actualizar los resultados.
    echo              Se mantienen los datos existentes.
    pause
    exit /b 1
)

echo.
echo [2/2] Recalculando ratings Elo con los nuevos resultados...
echo.
python data\generate_elo_ratings.py
if errorlevel 1 (
    echo.
    echo [ERROR] Fallo al recalcular los ratings Elo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  ACTUALIZACION COMPLETADA EXITOSAMENTE
echo.
echo  Los datos ahora incluyen los ultimos partidos de
echo  selecciones nacionales disponibles en la base publica.
echo.
echo  -> Reinicia el servidor (run.bat) para aplicar cambios.
echo ============================================================
echo.
pause
