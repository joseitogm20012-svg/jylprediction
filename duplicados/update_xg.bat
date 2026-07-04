@echo off
cd /d "%~dp0"
echo ============================================================
echo  Actualizando xG reales desde FBref (Mundial 2018/2022/2026)
echo ============================================================
echo.
python data\fetch_fbref_xg.py
echo.
echo Listo. Los datos de xG han sido actualizados.
pause
