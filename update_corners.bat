@echo off
echo ========================================
echo  Actualizar datos de corners (hybrid)
echo  Fuentes: Soccerway + FlashScore
echo ========================================

REM Activar entorno virtual
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

REM Ejecutar scraper híbrido
python scrapycoco\scrape_corners_hybrid.py --update

REM Revisar log
echo Log en: logs\corners_scraper.log

echo.
echo Hecho. Reinicia el servidor si esta corriendo.
pause
