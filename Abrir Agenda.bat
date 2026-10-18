@echo off
rem Abre la agenda de remates con la base real (agendar_remates.db). Doble clic.
cd /d "%~dp0"
start "Agenda de remates" /min ".venv\Scripts\python.exe" -m interfaz.servidor
