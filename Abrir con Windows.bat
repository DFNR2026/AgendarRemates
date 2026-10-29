@echo off
rem Hace que la agenda se abra sola al encender Windows (pedido de Diego, 29 de Octubre). Doble clic una sola vez.
rem Deja el acceso "Agenda de Remates" en la carpeta de Inicio de Windows. Para deshacerlo, borra ese acceso de esa carpeta.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$d=[Environment]::GetFolderPath('Startup'); $s=(New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $d 'Agenda de Remates.lnk')); $s.TargetPath=(Join-Path $pwd.Path 'Abrir Agenda.bat'); $s.WorkingDirectory=$pwd.Path; $s.WindowStyle=7; $s.Description='Abre la agenda de remates al encender Windows'; $s.Save(); Write-Host ('Listo. La agenda se abrira sola al encender Windows. Acceso en ' + $d)"
pause
