@echo off
rem Crea en el escritorio el acceso directo "Agenda de Remates" que abre la agenda. Doble clic una sola vez.
rem Lo arma el propio Windows, porque el que se hizo desde la nube no funcionaba (18 de Octubre).
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$d=[Environment]::GetFolderPath('Desktop'); $s=(New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $d 'Agenda de Remates.lnk')); $s.TargetPath=(Join-Path $pwd.Path 'Abrir Agenda.bat'); $s.WorkingDirectory=$pwd.Path; $s.Description='Abre la agenda de remates'; $s.Save(); Write-Host ('Listo. Acceso directo creado en ' + $d)"
pause
