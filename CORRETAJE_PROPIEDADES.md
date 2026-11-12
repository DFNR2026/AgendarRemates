# Corretaje de propiedades (lo que enseñó Diego)

Tema para profundizar más adelante. Por ahora queda lo que Diego explicó el 12 de Noviembre de 2026.

## Lo que enseñó Diego

1. Hay dos tipos de remate, el juicio ejecutivo de cobro de pesos y el de ley de bancos.
2. En el ejecutivo de cobro de pesos el mínimo de la subasta es la tasación fiscal de la propiedad del semestre en que se remata.
3. El mínimo NO dicta el precio final. Ejemplo. Si la deuda es de 100 millones y el mínimo de 30 millones, el banco demandante es el primero en pujar y ofrece los 100 millones, lo que deja el mínimo sin efecto. La deuda encarece la propiedad y la hace poco atractiva para revender con ganancia.
4. El caso ideal para comprar barato es el contrario, cuando la deuda del mandamiento es MENOR que el mínimo. El banco no tiene por qué subir el precio y queda margen para la compra y la reventa.
5. Al calcular el margen hay que sumar los gastos pendientes de la propiedad. Electricidad, derechos de aseo (se consultan en la municipalidad), gastos comunes si es condominio de departamentos o casas, y otros.

## Caso de ejemplo. C-15362-2025 del 11° Juzgado Civil de Santiago

Documentos en Corretaje\C-15362-2025 (mandamiento y acta de remate que pasó Diego).

- Juicio ejecutivo, Banco Santander-Chile. El aviso lo publicó El Mercurio el 21 y 22 de Octubre de 2026 (verificado en la base).
- Mínimo $66.762.980, garantía con vale vista nominativo al tribunal del 10% del mínimo, remate presencial (verificado en la base).
- Mandamiento del 24 de Diciembre de 2025 por 805,1377 UF, equivalentes a $31.902.116 al 5 de Noviembre de 2025, más intereses y costas (verificado en el PDF). La deuda es menos de la mitad del mínimo. Según Diego, el banco no hizo posturas.
- Acta de remate del 11 de Noviembre de 2026 (verificado en el PDF). Se presentaron 13 postores y se adjudicó en $99.000.000 a una inmobiliaria, con un vale vista de $6.700.000 (más que el 10% del mínimo, que era $6.676.298).

Observación de Claude (no la dijo Diego, queda para conversarla). Aunque el banco no pujó, la competencia de 13 postores subió el precio a $99.000.000, que es 1,48 veces el mínimo y 3,1 veces la deuda del mandamiento. O sea, el margen también depende de cuántos postores lleguen, no solo de la deuda. El vale vista del ganador también muestra que la garantía es un mínimo y se puede llevar más.

## Ideas para más adelante (sin decidir)

- Que el programa muestre la deuda del mandamiento junto al mínimo para ver el margen. Hoy el aviso no trae la deuda, hay que sacarla del expediente.
  EL GRAN PROBLEMA (Diego, 12 de Noviembre). El mandamiento está siempre en la Oficina Judicial Virtual (oficinajudicialvirtual.pjud.cl), que tiene una protección fuerte contra la automatización (WAF y bloqueo por IP). Eso impide automatizar el delta teórico que quiere Diego, VALOR COMERCIAL / MANDAMIENTO.
  Camino sin saltarse esa protección (idea de Claude, sin decidir). Diego descarga a mano el PDF del mandamiento con su Clave Única y lo deja en una carpeta de la causa. El programa lo lee de ahí. El mandamiento de C-15362-2025 trae texto (no es escaneado), así que el monto se puede leer con código. Falta definir de dónde sale el valor comercial.
  PRUEBA del 12 de Noviembre (Claude en el Chrome de Diego, a paso de persona, sin saltarse ninguna protección). SÍ se llega al mandamiento sin Clave Única. Oficina Judicial Virtual, Consulta causas, Búsqueda por RIT como Invitado. Competencia Civil, C.A. de Santiago, 11° Juzgado Civil de Santiago, rol 15362, año 2025. La causa aparece, el detalle muestra el cuaderno "2 Apremio Ejecutivo Obligación de Dar" con el Mandamiento en el folio 1 (24 de Diciembre de 2025) y el Acta de remate en el folio 21 (11 de Noviembre de 2026), y el PDF del mandamiento se abre y se lee (805,1377 UF, $31.902.116). La página tiene reCAPTCHA (versión invisible, el sello abajo a la derecha) y cada documento se abre con una clave cifrada propia de unos 400 caracteres, no con un enlace fijo, así que no hay una dirección directa al PDF.
  Conclusión. A mano o con Claude manejando el Chrome de Diego para unas pocas causas elegidas sí se puede. Un programa propio que consulte muchas causas solo, sin navegador, NO se probó y es justo lo que el reCAPTCHA y el WAF están hechos para frenar. No se intentará saltarlos. Falta leer las Condiciones de uso de la Consulta causas antes de cualquier uso repetido.
  Ojo. El mandamiento es la deuda a una fecha (805,1377 UF al 5 de Noviembre de 2025 en el ejemplo). Al día del remate la deuda real es mayor por intereses y costas.
- Registrar el resultado de los remates (precio de adjudicación y número de postores) para aprender cuánto sube el precio sobre el mínimo.
