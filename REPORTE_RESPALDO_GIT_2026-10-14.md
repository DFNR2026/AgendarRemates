# Reporte de respaldo git - 2026-10-14

Repositorio: https://github.com/DFNR2026/AgendarRemates
Visibilidad confirmada: PRIVATE (`gh repo view DFNR2026/AgendarRemates --json visibility` -> `{"visibility":"PRIVATE"}`)
Commit: 7f68909 (rama master, remoto origin/master)
Mensaje: Respaldo inicial: estado del proyecto, auditoría de la lectura del Mercurio, reconocimiento de 36 ediciones y banco de pruebas nivel 1

## Paso 1
git version 2.53.0.windows.1
gh version 2.96.0 (2026-07-02)
gh auth: Logged in to github.com account DFNR2026 (keyring); scopes: gist, read:org, repo

## Paso 2 - Inventario (bytes)
AUDITORIA_LECTURA_MERCURIO_2026-10-14.md 4949
ESTADO_PROYECTO.md 5250
RECONOCIMIENTO_EDICIONES_2026-10-14.md 3993
banco_pruebas/LEEME_BANCO_PRUEBAS.md 2731
banco_pruebas/Reporte_2026-08-06.xlsx 11827
banco_pruebas/Reporte_2026-10-14.xlsx 7938
banco_pruebas/2026-08-06/inventario_correcto_2026-08-06.json 13125
banco_pruebas/2026-08-06/payload_B-20260806-011.0.txt 43608
banco_pruebas/2026-08-06/payload_B-20260806-011.1.txt 39419
banco_pruebas/2026-08-06/payload_B-20260806-012.0.txt 44718
banco_pruebas/2026-08-06/payload_B-20260806-012.1.txt 40532
banco_pruebas/2026-08-06/payload_B-20260806-013.0.txt 43614
banco_pruebas/2026-08-06/payload_B-20260806-013.1.txt 39492
banco_pruebas/2026-10-14/HUELLAS_ESPERADAS.txt 373
banco_pruebas/2026-10-14/inventario_correcto_2026-10-14.json 8283
banco_pruebas/2026-10-14/mercurio_2026-10-14_B11.txt 88317
banco_pruebas/2026-10-14/mercurio_2026-10-14_C8.txt 88174

## Paso 3 - Huellas (original)
B11 9861D3D46FC8D700991CF3D3ACBA14BD8FEB519021CFBB89C5340715A96FF51A
C8  54EC1104EBD489ABC9402B63FEDDC0A6187002E4D834C43085C507DD807CFF45
Coinciden con HUELLAS_ESPERADAS.txt (9861d3d4...ff51a y 54ec1104...cff45).

## Pasos 4-5
.gitignore (config.py, .venv/, __pycache__/, *.pyc, logs/, *.log, .env); .gitattributes (`* -text`); git init; core.autocrlf = false.

## Paso 6 - git status --short
19 archivos con "A", ninguno "??".

## Paso 7 - Commit
[master (root-commit) 7f68909] ... 19 files changed, 11999 insertions(+)

## Paso 8
https://github.com/DFNR2026/AgendarRemates ; visibilidad PRIVATE.
origin https://github.com/DFNR2026/AgendarRemates.git

## Paso 10 - Push (aprobado por Diego: "apruebo push")
 * [new branch]      HEAD -> master
branch 'master' set up to track 'origin/master'.

## Paso 11 - Verificación en clon temporal (carpeta temporal borrada después)
git log --oneline del clon: 7f68909
B11 9861D3D46FC8D700991CF3D3ACBA14BD8FEB519021CFBB89C5340715A96FF51A
C8  54EC1104EBD489ABC9402B63FEDDC0A6187002E4D834C43085C507DD807CFF45
Resultado: COINCIDEN con HUELLAS_ESPERADAS.txt.

Este reporte no fue incluido en ningún commit.
