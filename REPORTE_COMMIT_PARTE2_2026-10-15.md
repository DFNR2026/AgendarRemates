# Reporte de commits parte 2 - 2026-10-15

No se hizo push. No se agregó "qué usa IA.png". No se muestran credenciales.

## Paso 1 - git status --short (14 líneas, coincide con la predicción ajustada)
```
 M ESTADO_PROYECTO.md
 M banco_pruebas/2026-10-14/inventario_correcto_2026-10-14.json
 M banco_pruebas/LEEME_BANCO_PRUEBAS.md
 M motor/lector_mercurio.py
?? BITACORA_2026-10-15.md
?? PROMPT_APERTURA_CHAT_NUEVO.md
?? banco_pruebas/2026-10-09/
?? banco_pruebas/2026-10-11/
?? banco_pruebas/2026-10-14/mercurio_2026-10-14_B11.geo.json
?? banco_pruebas/2026-10-14/mercurio_2026-10-14_C8.geo.json
?? motor/cortador.py
?? motor/orden_columnas.py
?? pruebas/test_cortador.py
?? "qu\303\251 usa IA.png"
```

## Paso 2 - Pruebas
test_cortador (verbatim):
```
=== 2026-08-06 ===
Avisos esperados 95 (93 con rol, 2 sin rol) | avisos cortados 95
Roles aislados correctamente 93 de 93
Roles inventados 0 []
Trozos sin rol 2 (esperados 2)
Trozos marcados para revisión o con dos roles 0

=== 2026-10-14 ===
Avisos esperados 59 (57 con rol, 2 sin rol) | avisos cortados 59
Roles aislados correctamente 57 de 57
Roles inventados 0 []
Trozos sin rol 2 (esperados 2)
Trozos marcados para revisión o con dos roles 0

=== 2026-10-14 (orden por posición) ===
Avisos esperados 59 (57 con rol, 2 sin rol) | avisos cortados 59
Roles aislados correctamente 57 de 57
Roles inventados 0 []
Trozos sin rol 2 (esperados 2)
Trozos marcados para revisión o con dos roles 0

=== 2026-10-11 F9 sola (orden por posición) ===
Avisos 19 (esperados 19) | dudosos [1] (esperado [1])

=== 2026-10-11 F15 sola (orden por posición) ===
Avisos 12 (esperados 12) | empleos dentro del rollo [] (esperado []) | dudosos [] (esperado []) | Temuco, Colina y partidor separados True

=== 2026-10-09 B11 sola (orden por posición) ===
Avisos 43 (esperados 43) | dudosos [10, 43] (esperado [10, 43]) | 1911 y 5598 bien partidos True

RESULTADO. TODO OK
```
test_navegacion_logica: termina en "RESULTADO. TODO OK".
Las tres líneas exigidas del cortador aparecen exactas.

## Paso 3 - Huellas SHA-256 (coinciden con la predicción)
- banco_pruebas\2026-10-14\mercurio_2026-10-14_B11.txt = 9861D3D46FC8D700991CF3D3ACBA14BD8FEB519021CFBB89C5340715A96FF51A
- banco_pruebas\2026-10-14\mercurio_2026-10-14_C8.txt  = 54EC1104EBD489ABC9402B63FEDDC0A6187002E4D834C43085C507DD807CFF45
- banco_pruebas\2026-10-11\mercurio_2026-10-11_F09.txt = B20A820BFE1D2CA56C7385522EFB491325A76AC0290FFBF5F350A394B361681B
- banco_pruebas\2026-10-11\mercurio_2026-10-11_F15.txt = FE2AD97F80E4B2E622C5F29EE9C11EAA5CBB1932E0ACD4FAA20BFD769A77984B

## Commits (hashes)
- A  0ebf8f5  Lector: guarda la posición de cada trozo de texto (.geo.json) junto al texto de cada página (1 archivo, +8 -2)
- B  96dd24c  Banco: inventario 14-10 corregido (59 avisos), posiciones impresas y casos de prueba F9/F15 del 11-10 y B11 del 09-10 (10 archivos, +4073 -2). Staging previo: exactamente 10 líneas de banco_pruebas.
- C  1dc399c  Motor parte 2: rollo único, corte por aviso y orden por posición en la página, con pruebas (3 archivos, +379)
- D  084a577  Documentos: estado y bitácora del 2026-10-15 (3 archivos: ESTADO_PROYECTO.md, BITACORA_2026-10-15.md, PROMPT_APERTURA_CHAT_NUEVO.md; +56 -4)

Cada mensaje lleva además la línea "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>".

## Paso 8
git status --short:
```
?? "qu\303\251 usa IA.png"
```
git log --oneline -5:
```
084a577 Documentos: estado y bitácora del 2026-10-15
1dc399c Motor parte 2: rollo único, corte por aviso y orden por posición en la página, con pruebas
96dd24c Banco: inventario 14-10 corregido (59 avisos), posiciones impresas y casos de prueba F9/F15 del 11-10 y B11 del 09-10
0ebf8f5 Lector: guarda la posición de cada trozo de texto (.geo.json) junto al texto de cada página
59ab712 Documentación: estado del proyecto, bitácora y reportes de la sesión 2026-10-14
```

## Verificación extra de credenciales
Antes del commit D se buscaron los valores reales de usuario y contraseña en lo preparado (git grep --cached, sin mostrarlos): 0 coincidencias.

## Diferencias contra las predicciones
Ninguna. Todas las salidas coincidieron.

Este reporte no se agregó a git (queda como archivo sin seguimiento).
