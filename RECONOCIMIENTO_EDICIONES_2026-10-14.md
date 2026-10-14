# Reconocimiento de ediciones del Mercurio (solo lectura, desde Chrome)

Hecho el 2026-10-14. Se revisaron 36 ediciones entre el 2026-06-04 y el 2026-10-14, todas las páginas de todos los cuerpos de cada día. Por página se buscó la cornisa "1616 Remates de propiedades" (c = cuántas veces aparece), los códigos de sección presentes (s) y las flechas de continuación. Formato por línea. fecha, día, cuerpos con su número de páginas, y las páginas con remates.

## Datos crudos

10/14 mié | A8 B12 C12 | B11(c5,s1611/1612/1616)[MAS→PÁGINA C 8] C8(c8,s1616/1635/1640)[←PÁGINA B 11]
10/13 mar | A8 B10 C10 | B8(c2) B9(c8)[MAS→PÁG. B 10] B10(c8)[←PÁGINA B 9]
10/12 lun | A10 B8 C10 | B6(c6) B7(c8)[MAS→PÁG. B 8] B8(c8)[←PÁGINA B 7]
10/11 dom | A26 B16 C16 E6 F16 R10 | F7 a F15 (9 páginas)
10/10 sáb | A12 B8 C16 D12 | D5 a D12 (8 páginas)
10/09 vie | A10 B14 C14 G12 | B11 a B13 y además G5 a G12
10/08 jue | A8 B14 C12 | B11 a B13
10/07 mié | A8 B12 C10 | B9 a B11
10/06 mar | A8 B10 C10 | B7, B8, B9[MAS→PÁG. B 10], B10[←PÁGINA B 9]
10/05 lun | A10 B10 C14 | B7 a B9
10/04 dom | A26 B22 C14 E6 F16 R10 T8 | F7 a F15
10/03 sáb | A10 B10 C12 D16 | D9 a D15
10/02 vie | A10 B14 C12 G12 | B11 a B13 y además G7 a G12
10/01 jue | A8 B16 C10 | B13 a B15
09/30 mié | A12 B18 C14 | B15 a B17
09/27 dom | A18 B22 C20 E6 F16 R14 | F8 a F15
09/26 sáb | A10 B12 C14 D12 | D6 a D12
09/23 mié | A8 B12 C10 | B10 a B11
09/20 dom | A10 B14 C12 E6 F12 R8 | F6 a F11
09/19 sáb | A8 B6 C10 D8 | D4 a D8
09/15 mar | A8 B12 C14 | B9 a B11
09/13 dom | A20 B20 C14 E6 F12 R8 | F7 a F12
09/12 sáb | A16 B10 C10 D12 | D6 a D12
09/08 mar | A8 B14 C10 | B11 a B13
09/06 dom | A26 B20 C14 E6 F12 R10 | F5 a F11
09/05 sáb | A10 B10 C12 D12 | D5 a D11
09/01 mar | A10 B16 C12 | B15[MAS→PÁG. C 8] y C8[←PÁGINA B 15]
08/30 dom | A28 B18 C16 E6 F12 R10 | F9 a F12
08/29 sáb | A14 B12 C14 D12 | D8 a D12
08/22 sáb | A12 B12 C14 D12 | D6 a D12
08/15 sáb | A10 B10 C12 D12 | D5 a D12
08/06 jue | A8 B14 C10 | B11 a B13
08/01 sáb | A12 B10 C16 D16 | D9 a D15
07/05 dom | A16 B16 C14 E6 F8 R8 | F6 a F8
07/04 sáb | A12 B10 C16 D8 | D6 a D8
06/04 jue | A8 B16 C8 P4 | B13 a B15

Páginas sin texto (imágenes, todas de publicidad o noticias en A, B o P). Ninguna cae dentro del rango de remates.

## Hallazgos (n = 36 ediciones)

1. Los remates viven en un solo cuerpo por día según el día de la semana. Lunes a viernes en B (n = 24), sábado en D (n = 9), domingo en F (n = 7). Siempre en las últimas páginas de ese cuerpo, en bloque seguido.
2. La continuación a otro cuerpo es rara. B hacia C 8 pasó 2 veces en 36 ediciones (09-01 escrito "PÁG. C 8" y 10-14 escrito "PÁGINA C 8"). En ambos casos C 8 trae la flecha de vuelta "VIENEN DE PÁGINA B ...".
3. La flecha también aparece entre páginas seguidas del mismo cuerpo (B 9 hacia B 10 los días 10-06, 10-12 y 10-13), así que no siempre significa salto a otro cuerpo.
4. La página que sigue a una flecha a veces tiene un código distinto al formato B-AAAAMMDD-NNN (por ejemplo 8A4MD0L7 o CB4M9JCN). No se puede suponer el formato del código.
5. Existe un cuerpo G los viernes (n = 2 de 2 viernes revisados) que repite los remates del cuerpo B. El 10-09 B tenía 119 roles y G 122, con 118 en común. Comprobado después. Los 4 roles que solo están en G son notificaciones de la sección 1611, no remates. Dentro de la sección 1616, G trae 117 roles y todos están en B (B trae 1 más, el C-3862-2025). Conclusión con n = 1 viernes comprobado. G es una reimpresión y B basta, pero el motor igual debe leer ambos y unir sin duplicar por si algún viernes difieren.
6. Hay otras flechas que no son de remates ("MÁS AVISOS DE DEFUNCIONES EN PÁG. C 6"). La regla debe exigir "AVISOS ECONÓMICOS CLASIFICADOS".
7. La cornisa "1616 Remates de propiedades" apareció en todas las páginas de remates de las 36 ediciones, de 1 a 8 veces por página. Es la marca más confiable para encontrar las páginas.
