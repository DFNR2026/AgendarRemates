@echo off
rem Abre la agenda con la base de PRUEBA (interfaz_prueba.db), para revisar la interfaz sin tocar la base real.
cd /d "%~dp0"
start "Agenda de remates (prueba)" /min ".venv\Scripts\python.exe" -m interfaz.servidor --base interfaz_prueba.db --puerto 8766
