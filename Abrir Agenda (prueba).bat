@echo off
rem Abre la agenda con la base de PRUEBA (interfaz_prueba.db), para revisar la interfaz sin tocar la base real.
cd /d "%~dp0"
rem Sin ventana negra desde el 29 de Octubre. La agenda se apaga sola unos 3 minutos despues de cerrar el navegador.
start "Agenda de remates (prueba)" ".venv\Scripts\pythonw.exe" -m interfaz.servidor --base interfaz_prueba.db --puerto 8766
