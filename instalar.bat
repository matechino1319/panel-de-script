@echo off
cd /d "%~dp0"
echo ============================================================
echo   Instalando dependencias...
echo ============================================================
echo.
pip install -r requirements.txt
echo.
echo ============================================================
echo   Listo. Ya podes levantar el servidor con iniciar.bat
echo ============================================================
pause
