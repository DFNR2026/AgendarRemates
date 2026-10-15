# Reporte commits parte 3A — 2026-10-15 (tarde)

## Paso 1. git status --short
14 líneas, idénticas a lo esperado.

## Paso 2. Pruebas
- pruebas.test_navegacion_logica: RESULTADO. TODO OK
- pruebas.test_cortador: RESULTADO. TODO OK
- pruebas.test_banco_nivel2: RESULTADO. TODO OK

Sección de test_cortador:
```
=== 2026-10-14 ===
Avisos esperados 61 (57 con rol, 4 sin rol) | avisos cortados 61
Roles aislados correctamente 57 de 57
Roles inventados 0 []
Trozos sin rol 4 (esperados 4)
Trozos marcados para revisión o con dos roles 0
```
test_banco_nivel2: `Remates en el banco 61 (esperados 61) | citas revisadas 431`

## Pasos 3 a 5. Commits
| Commit | Hash | Archivos |
|---|---|---|
| A, motor | ddd45fd | 2 |
| B, banco de pruebas | 84c76d2 | 5 |
| C, documentos | 760d8a8 | 5 |

- Commit B: `git diff --cached --name-only` mostró exactamente los 5 archivos pedidos.
- Commit C: búsqueda de usuario y contraseña de config.py (MERCURIO_USER y MERCURIO_PASS) con `git grep --cached -F`: 0 coincidencias. Los valores no se mostraron.

## Paso 6
git status --short:
```
?? banco_pruebas/2026-10-14/REVISION_DIEGO_nivel2_2026-10-14.xlsx
?? "qu\303\251 usa IA.png"
```
git log --oneline -5:
```
760d8a8 Documentos: estado, bitácora y preguntas para el abogado de la tarde del 2026-10-15
84c76d2 Banco: inventario 14-10 corregido a 61 avisos y banco nivel 2 (61 remates con citas) con su prueba
ddd45fd Cortador: separa avisos sin rol que empiezan con JUEZ PARTIDOR o PRIMER/SEGUNDO/TERCER LLAMADO (iban pegados al aviso anterior en 5 de 7 fechas)
084a577 Documentos: estado y bitácora del 2026-10-15
1dc399c Motor parte 2: rollo único, corte por aviso y orden por posición en la página, con pruebas
```
No se hizo push.

## Diferencias contra lo esperado
Ninguna.
