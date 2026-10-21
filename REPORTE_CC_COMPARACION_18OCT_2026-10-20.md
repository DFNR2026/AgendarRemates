# Reporte de la comparación del ensayo en la nube con la captura local del 18 de Octubre

Hecho el 20 de Octubre de 2026 por la noche, en el PC de Diego. No se modificó ni reemplazó nada en capturas, no se tocó agendar_remates.db y no se mostró ninguna clave. No se modificó código. Este reporte no se agregó a git.

## El ensayo
- Comando gh workflow run diario.yml con modo ensayo, fecha 2026-10-18 y origen manual.
- Corrida número 39531376280 (https://github.com/DFNR2026/AgendarRemates/actions/runs/39531376280).
- Quedó en verde y duró 2 minutos y 55 segundos (el ensayo anterior del 20 de Octubre había durado 6 minutos y 23 segundos, porque esa vez Haiku tuvo que leer 100 avisos nuevos).
- Única anotación del flujo, el aviso conocido de que Node.js 20 está obsoleto para actions/checkout@v4 y actions/setup-python@v5.
- El registro completo (606 líneas) no tenía ningún texto con forma de clave de Anthropic.

### Líneas [diario] del registro, tal cual
```
[diario] Edición 2026-10-18. Modo ensayo. Hora de Chile 23:09. Último intento sí.
[diario] Intento número 1.
[diario] Respuestas de Haiku disponibles 823.
[diario] Lectura. Código 0. Páginas de remates 8. Sin problemas.
[diario] Carga de paso. {'paginas': 8, 'avisos': 144, 'remates': 147, 'vale_vista': {'leidos': 127, 'sin_ia': 0, 'colores': {'verde': 80, 'ambar': 18, 'rojo': 23, 'sin_dato': 6}}, 'direccion': {'leidos': 127, 'sin_ia': 0, 'colores': {'verde': 119, 'rojo': 8}}, 'respuestas_nuevas': 0}
[diario] Marca listo. 
```
Las respuestas de Haiku disponibles fueron 823 (las 723 de git más las 100 que dejó el ensayo anterior) y las respuestas nuevas fueron cero, o sea que esta vez no se llamó a Haiku porque todos los avisos ya tenían respuesta guardada.

### Marca pruebas/ensayo/marcas/2026-10-18.json, completa
```
{
  "fecha": "2026-10-18",
  "estado": "listo",
  "motivo": null,
  "intentos": 1,
  "hora": "2026-10-20T23:09",
  "modo": "ensayo",
  "paginas": 8,
  "avisos": 144,
  "remates": 147,
  "vale_vista": {
    "leidos": 127,
    "sin_ia": 0,
    "colores": { "verde": 80, "ambar": 18, "rojo": 23, "sin_dato": 6 }
  },
  "direccion": {
    "leidos": 127,
    "sin_ia": 0,
    "colores": { "verde": 119, "rojo": 8 }
  },
  "respuestas_nuevas": 0
}
```
(Los colores se muestran en una sola línea para ahorrar espacio, los valores son los mismos.) La marca real marcas/2026-10-18.json no existe, como corresponde a un ensayo.

## La comparación
El zip pruebas/ensayo/capturas/2026-10-18.zip (251.409 bytes, 17 archivos) se bajó a una carpeta temporal fuera del proyecto, ya borrada. Se comparó con D:\Agendar_Remates\capturas\2026-10-18, que antes y después de la comparación tenía 17 archivos, sin cambios.

### Textos de las páginas (sha256)
- Archivos .txt en la captura local 8 y en la nube 8. Ninguno solo en un lado.
- **Idénticas 8 de 8. Diferentes 0.**

| Página | Archivo | Primeros 16 caracteres del sha256 | Resultado |
|---|---|---|---|
| F8 | F08_T94MCVVL.txt | 435ca4587e5b5897 | Idéntica |
| F9 | F09_T94MCVVM.txt | 3c0bd1b4ab1ac17b | Idéntica |
| F10 | F10_T94MCVVN.txt | 27d8395402a75ad3 | Idéntica |
| F11 | F11_T94MCVVO.txt | 8a9365964fbe4c7c | Idéntica |
| F12 | F12_TL4MGGDB.txt | 0ad540bdce6bccfe | Idéntica |
| F13 | F13_TL4MGGDC.txt | 03e40d7e8df0af14 | Idéntica |
| F14 | F14_TL4MGGDD.txt | 744c9833dbc0ceb7 | Idéntica |
| F15 | F15_TL4MGGDE.txt | 7c9928bb3a915d37 | Idéntica |

Como dato extra, los 8 archivos .geo.json de posiciones también son idénticos en los dos lados.

### navegacion.json
- Campo cuerpos. Igual. Valor en los dos lados A n=24, B n=26, C n=14, E n=6, F n=16 y R n=10, todos de la edición 2026/10/18.
- Campo rollos. Igual. Un solo rollo, F8-F9-F10-F11-F12-F13-F14-F15.
- Lista paginas_con_remates. Igual. Ocho páginas, con el mismo id, archivo, número de cornisas, salidas, entradas, caracteres y sha256 en cada una.
- Los únicos campos que difieren son los de la hora de lectura, como era de esperar. leida_en local 2026-10-18T22:25:51 y nube 2026-10-20T23:09:36. segundos local 54 y nube 128.

## Conclusión
La nube leyó la edición del 18 de Octubre exactamente igual que el PC. Las ocho páginas son idénticas byte a byte, la navegación coincide y la carga de paso dio 144 avisos y 147 remates, que son las mismas cifras de la carga de referencia del 18 de Octubre. Sin diferencias.

## Cosas a tener en cuenta
- Como la corrida usó las 823 respuestas ya guardadas, no probó que Haiku se llame bien para avisos nuevos. Eso sí lo probó el ensayo anterior del 20 de Octubre (100 respuestas nuevas).
- El ensayo no usó la marca real ni las capturas reales, solo la carpeta pruebas/ensayo.

Diego, vuelve al chat con Claude para revisar este reporte.
