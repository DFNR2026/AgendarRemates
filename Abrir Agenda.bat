@echo off
rem Abre la agenda de remates con la base real (agendar_remates.db). Doble clic.
cd /d "%~dp0"
rem Sin ventana negra desde el 29 de Octubre. La agenda se apaga sola unos 3 minutos despues de cerrar el navegador.
start "Agenda de remates" ".venv\Scripts\pythonw.exe" -m interfaz.servidor
