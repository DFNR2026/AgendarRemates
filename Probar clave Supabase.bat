@echo off
cd /d "%~dp0"
.venv\Scripts\python.exe -m interfaz.probar_clave
echo.
echo Listo. El resultado quedo en logs\prueba_clave.txt
pause
