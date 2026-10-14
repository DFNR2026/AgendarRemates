# Auditoría de la lectura del Mercurio (solo lectura)

Fecha 2026-10-14. Base de código revisada en D:\Mercurio, último commit 94fe275. No se modificó ningún archivo del Mercurio.

Muestra usada. Edición del 06-08-2026 (textLayer completo guardado en payloads_diag_v2, 3 páginas, y su Excel Reporte_2026-08-06.xlsx) más el log de la corrida del 14-10-2026. Toda conclusión vale para n = 1 edición completa.

## Lo que salió bien

En la edición del 06-08 los 81 roles del Excel (24 en tabla principal, 33 excluidos por CBR, 24 descartados) existen en el texto del diario. Cero roles inventados en esa muestra. En las 24 causas principales la fojas y la comuna aparecen en el texto cercano al rol. Los roles del texto que no llegaron al Excel son remates de vehículos y muebles (correcto) o causas ya en el historial (diseño).

## Mecanismos de error encontrados

1. Avisos partidos entre páginas (verificado). Cada página se manda sola a la IA. El aviso del 23° Juzgado Civil, rol C-14821-2023, empieza al final de la página 012 y termina al inicio de la 013. La mitad con el encabezado no tiene rol y se bota en silencio. La mitad con el rol no tiene tribunal y terminó descartada como "Solo RM". En la corrida de diagnóstico DeepSeek le puso tribunal "23° Juzgado Civil" a esa mitad aunque el trozo no lo dice, o sea completó el dato adivinando por los avisos vecinos. Este es el candidato principal para ambos síntomas reportados.

2. Avisos partidos dentro de una misma página (mecanismo verificado en el código, frecuencia no medida). Las páginas de más de 45.000 caracteres se cortan en dos con un solape de 2.000 caracteres, pero hay avisos de hasta 7.500 caracteres. Un aviso largo cortado en el medio queda incompleto en ambos trozos.

3. Avisos sin rol impreso se botan en silencio (verificado, n = 2). El aviso del 3er Juzgado Civil contra Iturra Saldías (06-08) no trae rol en el diario y el del 7° Juzgado Civil en Puente Alto (14-10) salió sin rol. Ambos solo quedan en el log de depuración, nunca en el Excel.

4. La IA omite datos que sí están (verificado, n = 1). El rol C-8383-2024 salió con tribunal vacío aunque su aviso empieza con "REMATE VIGÉSIMO TERCER JUZGADO". El código no fija la temperatura, así que la misma página puede dar resultados distintos en cada corrida.

5. El historial congela los errores (verificado en el código). Si una causa se registra con datos faltantes, sus republicaciones de los días siguientes se descartan por duplicadas y nunca la completan.

6. Año de rol no legible se descarta sin quedar registrado en ninguna tabla (verificado en el código).

## Pendiente

Pedir al abogado dos o tres casos concretos (fecha del diario y rol) de causa inventada y de dato faltante, para confirmar contra estos mecanismos. La causa de las "causas inventadas" no quedó demostrada con esta muestra.

## Consecuencias para Agendar_Remates

Unir el texto de todas las páginas en orden de lectura antes de cortar. Cortar por avisos completos y nunca por tamaño. No botar jamás un aviso sin rol, mostrarlo como "sin rol". Exigir a la IA la cita textual de cada dato y verificarla con código. Fijar temperatura en cero.

## Segunda verificación con la edición del 14-10-2026

Texto leído directo del visor del diario en Chrome. La página B 11 dio exactamente los mismos largos de trozo que registra el log (46.183 y 42.187 caracteres), así que es el mismo texto que recibió la IA.

7. Redirección a otra página no detectada (verificado, el error más grave). Al final de la página B 11 el diario dice "MÁS AVISOS ECONÓMICOS CLASIFICADOS EN PÁGINA C 8". El patrón del código busca "PÁG." y no reconoce "PÁGINA", así que la página C 8 nunca se leyó. Esa página trae unos 33 avisos más de la sección 1616. Ese día el programa leyó 19 avisos con rol y dejó fuera más de la mitad de los remates. No se sabe desde cuándo el diario usa "PÁGINA".

8. Datos cruzados en el corte de la página (verificado el resultado, la explicación tiene confianza de 75 %). La página B 11 se cortó en el carácter 46.183, justo dentro del aviso del rol C-8715-2025. Resultados. El rol C-14116-2025 aparece en la tabla de excluidos por CBR con dominio 2022, pero su aviso dice año 2008. Además aparece dos veces en el Excel, una en excluidos y otra en descartados por Banco Estado. El rol C-8715-2025 salió en la tabla principal sin dirección, sin comuna y sin fojas, aunque el aviso trae Avenida Pajaritos 3195, Maipú, fojas 10674 y 10675, año 2022. Con ese año debió quedar excluido por CBR. Lo más probable es que el 2022 del aviso 8715 se le pegó al 14116.

9. El último aviso de B 11 (7° Juzgado Civil, Puente Alto) sigue en C 8, donde aparece su rol C-5849-2026. Como C 8 no se leyó, quedó botado por falta de rol.

Lo verificado sin error ese día. Los 19 roles con aviso en B 11 están en el texto. Ningún rol inventado (n = 2 ediciones).
