-- Esquema de la base de Agendar_Remates (SQLite). Versión 2, 2026-10-15.
-- Cambios de la parte 3.5 aprobados por Diego el 2026-10-15.
-- Un aviso (lo impreso) puede traer varios remates. Cada remate apunta a un bien (causa + inmueble),
-- que es la identidad que sobrevive a las republicaciones. La agenda va por bien, o sea por remate.
-- Las vistas van al final. Se borran y se vuelven a crear cada vez (no guardan datos), así siempre quedan al día.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS meta (
  clave TEXT PRIMARY KEY,
  valor TEXT NOT NULL
);

-- 1. EDICIONES. Un registro por diario leído.
CREATE TABLE IF NOT EXISTS ediciones (
  id                 INTEGER PRIMARY KEY,
  fecha              TEXT NOT NULL UNIQUE,          -- AAAA-MM-DD de la edición
  leida_en           TEXT NOT NULL,                 -- fecha y hora de la lectura
  estado             TEXT NOT NULL CHECK (estado IN ('ok','con_alarmas','fallida')),
  cuerpos_revisados  TEXT,                          -- ej. "A8 B12 C12"
  roles_en_texto     INTEGER,                       -- roles que el código contó en el texto
  avisos_extraidos   INTEGER,                       -- avisos guardados, incluidos los descartados (deben cuadrar)
  remates_extraidos  INTEGER,                       -- remates guardados (un aviso puede traer varios)
  alarmas            TEXT                           -- una alarma por línea, vacío si cuadró todo
);

-- 2. PÁGINAS. La evidencia. Texto completo de cada página con remates.
CREATE TABLE IF NOT EXISTS paginas (
  id            INTEGER PRIMARY KEY,
  edicion_id    INTEGER NOT NULL REFERENCES ediciones(id) ON DELETE CASCADE,
  cuerpo        TEXT NOT NULL,                      -- B, C, D, F, G...
  numero        INTEGER NOT NULL,                   -- número de página dentro del cuerpo
  id_pagina     TEXT NOT NULL,                      -- código del visor. No tiene formato fijo (B-20261014-011, L64MFDBT)
  ruta          TEXT NOT NULL UNIQUE,               -- ej. /2026/10/14/C/L64MFDBT. El link = dirección base de config.py + ruta
  orden_rollo   INTEGER,                            -- posición en el rollo unido
  cornisas_1616 INTEGER NOT NULL DEFAULT 0,
  flechas       TEXT,                               -- "MÁS AVISOS..." y "VIENEN DE..." encontradas
  texto         TEXT NOT NULL,
  sha256        TEXT NOT NULL,
  UNIQUE (edicion_id, cuerpo, numero)
);

-- 5. CAUSAS. El juicio (rol-año más tribunal). Un juicio puede rematar muchos bienes.
CREATE TABLE IF NOT EXISTS causas (
  id          INTEGER PRIMARY KEY,
  clave       TEXT NOT NULL UNIQUE,                 -- rol-año|tribunal normalizado (misma llave del Mercurio)
  tipo_id     TEXT NOT NULL CHECK (tipo_id IN ('ROL','RIT')),
  rol         TEXT NOT NULL,                        -- solo dígitos
  anio        TEXT NOT NULL,
  tribunal    TEXT NOT NULL,
  corte       TEXT
);

-- 5c. BIENES. Lo que se remata, con identidad estable entre publicaciones (causa + inmueble).
-- Regla aprobada. Si la causa trae un solo remate en ambas publicaciones se unen por causa. Si trae varios,
-- por número de depto, lote u oficina. Si no calza, alerta "posible republicación" en vez de adivinar.
CREATE TABLE IF NOT EXISTS bienes (
  id          INTEGER PRIMARY KEY,
  causa_id    INTEGER REFERENCES causas(id),        -- NULL si el aviso no trae rol ni RIT
  clave       TEXT NOT NULL UNIQUE,                 -- la arma el código según la regla de arriba
  inmueble    TEXT,                                 -- ej. "oficina 602", "Lote 1", NULL si la causa remata un solo bien
  creado_en   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_bienes_causa ON bienes(causa_id);

-- 3. AVISOS. Una fila por publicación de un aviso en una edición. Lo común a todos sus remates.
CREATE TABLE IF NOT EXISTS avisos (
  id                  INTEGER PRIMARY KEY,
  edicion_id          INTEGER NOT NULL REFERENCES ediciones(id) ON DELETE CASCADE,
  causa_id            INTEGER REFERENCES causas(id),   -- NULL si el aviso no trae rol ni RIT
  orden               INTEGER NOT NULL,                -- posición del aviso en el rollo (el n del cortador)
  pagina_inicio_id    INTEGER REFERENCES paginas(id),  -- para el link directo
  pagina_fin_id       INTEGER REFERENCES paginas(id),  -- distinta de la de inicio si el aviso va partido
  texto               TEXT NOT NULL,                   -- texto completo del aviso
  rol_impreso         TEXT,                            -- tal como viene en el diario (C-39902025, CC-936-2026...)
  tipo_id             TEXT CHECK (tipo_id IN ('ROL','RIT','SIN_ROL')),
  rol                 TEXT,
  anio                TEXT,
  tribunal            TEXT,
  corte               TEXT,
  demandante          TEXT,
  demandado           TEXT,
  fojas               TEXT,
  anio_dominio        INTEGER,
  -- pasa. se ve. fuera_filtro. se ve marcado con su motivo. descartado. JUEZ PARTIDOR, no aparece en
  -- ninguna búsqueda ni vista de Diego, existe solo para el cuadre de cuentas.
  filtro_estado       TEXT NOT NULL DEFAULT 'pasa' CHECK (filtro_estado IN ('pasa','fuera_filtro','descartado')),
  filtro_motivos      TEXT,                            -- ej. "BancoEstado; dominio 2022" o "juez partidor"
  verificacion        TEXT NOT NULL DEFAULT 'pendiente' CHECK (verificacion IN ('completa','con_rojos','pendiente')),
  UNIQUE (edicion_id, orden)
);
CREATE INDEX IF NOT EXISTS ix_avisos_rol ON avisos(rol, anio);
CREATE INDEX IF NOT EXISTS ix_avisos_tribunal ON avisos(tribunal);
CREATE INDEX IF NOT EXISTS ix_avisos_causa ON avisos(causa_id);

-- 3b. REMATES. Una fila por remate dentro de un aviso (el aviso 30 del 14 de Octubre trae 4 lotes).
CREATE TABLE IF NOT EXISTS remates (
  id                  INTEGER PRIMARY KEY,
  aviso_id            INTEGER NOT NULL REFERENCES avisos(id) ON DELETE CASCADE,
  sub_orden           INTEGER NOT NULL CHECK (sub_orden >= 1),   -- 1, 2, 3... dentro del aviso
  bien_id             INTEGER REFERENCES bienes(id),             -- NULL hasta que el código lo une
  inmueble            TEXT,                                      -- ej. "oficina 602", "Lote 1"
  direccion           TEXT,
  comuna              TEXT,
  fecha_remate        TEXT,                                      -- AAAA-MM-DD
  hora_remate         TEXT,                                      -- HH:MM
  modalidad           TEXT CHECK (modalidad IN ('zoom','presencial','mixta','en_linea','sin_dato')),
  plataforma          TEXT,                                      -- ej. Google Meet, vendaya.cl (para en_linea)
  minimo_monto        REAL,
  minimo_moneda       TEXT CHECK (minimo_moneda IN ('CLP','UF')),
  minimo_costas_clp   REAL,                                      -- cuando el mínimo suma costas aparte (aviso 17)
  garantia_porcentaje REAL,                                      -- ej. 10 si dice "10% del mínimo"
  garantia_base       TEXT CHECK (garantia_base IN ('minimo','tasacion','sin_dato')),
  garantia_monto      REAL,                                      -- si el aviso da un monto fijo (puede venir junto al porcentaje)
  garantia_moneda     TEXT CHECK (garantia_moneda IN ('CLP','UF')),
  vv_regla            TEXT,                                      -- código de la regla (dias_habiles_antes, dia_anterior...). Vocabulario abierto
  vv_regla_texto      TEXT,                                      -- la regla con las palabras del aviso
  vv_desde            TEXT,                                      -- AAAA-MM-DD o AAAA-MM-DD HH:MM calculado por código
  vv_desde_origen     TEXT CHECK (vv_desde_origen IN ('texto','estimado_dia_siguiente_edicion')),
  vv_hasta            TEXT,
  vv_estado           TEXT CHECK (vv_estado IN ('calculado','revisar','sin_dato')),
  UNIQUE (aviso_id, sub_orden)
);
CREATE INDEX IF NOT EXISTS ix_remates_fecha ON remates(fecha_remate);
CREATE INDEX IF NOT EXISTS ix_remates_bien ON remates(bien_id);

-- 4. CITAS. El candado contra datos inventados. Una o varias frases por dato.
CREATE TABLE IF NOT EXISTS citas (
  id          INTEGER PRIMARY KEY,
  aviso_id    INTEGER NOT NULL REFERENCES avisos(id) ON DELETE CASCADE,
  sub_orden   INTEGER NOT NULL DEFAULT 0 CHECK (sub_orden >= 0),  -- 0 = dato del aviso completo, 1.. = dato de ese remate
  campo       TEXT NOT NULL,                        -- nombre de la columna de avisos o remates
  n_cita      INTEGER NOT NULL DEFAULT 1 CHECK (n_cita >= 1),     -- 2, 3... para citas extra del mismo dato
  valor       TEXT,
  cita        TEXT,                                 -- frase exacta del diario
  metodo      TEXT NOT NULL CHECK (metodo IN ('codigo','ia')),
  verificada  INTEGER NOT NULL CHECK (verificada IN (0,1)),  -- 1 si el código encontró la cita en el texto del aviso
  UNIQUE (aviso_id, sub_orden, campo, n_cita)
);

-- 4b. ALERTAS. Lo que la ficha del remate debe destacar, junto al link a la página del diario.
CREATE TABLE IF NOT EXISTS alertas (
  id          INTEGER PRIMARY KEY,
  aviso_id    INTEGER NOT NULL REFERENCES avisos(id) ON DELETE CASCADE,
  sub_orden   INTEGER NOT NULL DEFAULT 0 CHECK (sub_orden >= 0),  -- 0 = todo el aviso
  -- error_escritura, rol_mal_impreso y contradiccion son errores del AVISO (podrían servir para anular).
  -- revisar_lectura es una duda de LECTURA del programa. condicion_especial y aviso_previo son condiciones del tribunal.
  -- posible_republicacion la pone el código cuando no puede unir un remate con su bien.
  -- dato_faltante es algo que el aviso no dice y que Diego debe resolver (ej. cuándo se entrega el vale vista).
  -- detalle_menor es un error de forma del aviso que se muestra con tono normal (ej. sin guion en el rol). Decisión de Diego.
  tipo        TEXT NOT NULL CHECK (tipo IN ('error_escritura','rol_mal_impreso','contradiccion',
                                            'condicion_especial','aviso_previo','revisar_lectura',
                                            'posible_republicacion','dato_faltante','detalle_menor')),
  texto       TEXT NOT NULL,
  cita        TEXT,
  origen      TEXT NOT NULL CHECK (origen IN ('codigo','ia')),
  visto       INTEGER NOT NULL DEFAULT 0 CHECK (visto IN (0,1))
);
CREATE INDEX IF NOT EXISTS ix_alertas_aviso ON alertas(aviso_id);

-- 5b. CAMBIOS ENTRE PUBLICACIONES de un mismo bien.
CREATE TABLE IF NOT EXISTS cambios (
  id               INTEGER PRIMARY KEY,
  bien_id          INTEGER NOT NULL REFERENCES bienes(id) ON DELETE CASCADE,
  remate_anterior  INTEGER NOT NULL REFERENCES remates(id),
  remate_nuevo     INTEGER NOT NULL REFERENCES remates(id),
  campo            TEXT NOT NULL,
  valor_anterior   TEXT,
  valor_nuevo      TEXT,
  detectado_en     TEXT NOT NULL,
  visto            INTEGER NOT NULL DEFAULT 0 CHECK (visto IN (0,1))
);

-- 6. MI AGENDA. Los remates que Diego elige (uno por bien, así puede elegir un solo lote).
-- Quitar del calendario = borrar la fila (botón X).
CREATE TABLE IF NOT EXISTS agenda (
  id              INTEGER PRIMARY KEY,
  bien_id         INTEGER NOT NULL UNIQUE REFERENCES bienes(id),
  remate_base_id  INTEGER NOT NULL REFERENCES remates(id),  -- publicación vigente cuando se agendó
  agregado_en     TEXT NOT NULL,
  vv_entregado    INTEGER NOT NULL DEFAULT 0 CHECK (vv_entregado IN (0,1)),
  remate_asistido INTEGER NOT NULL DEFAULT 0 CHECK (remate_asistido IN (0,1)),
  notas           TEXT
);

-- 7. FERIADOS. Para calcular reglas como "el viernes anterior, o el día hábil anterior si es feriado".
CREATE TABLE IF NOT EXISTS feriados (
  fecha   TEXT PRIMARY KEY,                         -- AAAA-MM-DD
  nombre  TEXT NOT NULL,
  ambito  TEXT NOT NULL CHECK (ambito IN ('nacional','regional')),
  fuente  TEXT NOT NULL
);

-- ============================================================================================
-- VISTAS (parte 3.5, etapa 3). Regla de Diego. Los avisos 'descartado' (JUEZ PARTIDOR) no aparecen
-- en NINGUNA vista. Solo existen en las tablas para el cuadre de cuentas.
-- Las fechas salen en formato AAAA-MM-DD. La interfaz las muestra con el mes en palabras (Nov.), nunca en número.
-- ============================================================================================

-- Buscador. Un renglón por remate visible. Diego busca por rol o tribunal en la edición elegida.
DROP VIEW IF EXISTS v_buscador;
CREATE VIEW v_buscador AS
  SELECT e.fecha AS edicion, a.id AS aviso_id, a.orden, r.id AS remate_id, r.sub_orden, r.bien_id,
         a.tipo_id, a.rol, a.anio, a.rol_impreso, a.tribunal, r.inmueble, r.direccion, r.comuna,
         r.fecha_remate, r.hora_remate, r.modalidad, r.plataforma,
         r.minimo_monto, r.minimo_moneda, r.minimo_costas_clp,
         r.garantia_porcentaje, r.garantia_base, r.garantia_monto, r.garantia_moneda,
         r.vv_regla_texto, r.vv_desde, r.vv_desde_origen, r.vv_hasta, r.vv_estado,
         a.filtro_estado, a.filtro_motivos, a.verificacion,
         pi.ruta AS ruta_inicio, CASE WHEN pf.id <> pi.id THEN pf.ruta END AS ruta_fin,
         (SELECT COUNT(*) FROM alertas x WHERE x.aviso_id = a.id AND x.sub_orden IN (0, r.sub_orden)) AS n_alertas,
         EXISTS (SELECT 1 FROM agenda g WHERE g.bien_id = r.bien_id) AS agendado
  FROM remates r
  JOIN avisos a ON a.id = r.aviso_id
  JOIN ediciones e ON e.id = a.edicion_id
  LEFT JOIN paginas pi ON pi.id = a.pagina_inicio_id
  LEFT JOIN paginas pf ON pf.id = a.pagina_fin_id
  WHERE a.filtro_estado <> 'descartado';

-- Alertas para la ficha del remate, con el link a la página del diario.
DROP VIEW IF EXISTS v_alertas;
CREATE VIEW v_alertas AS
  SELECT e.fecha AS edicion, a.id AS aviso_id, a.orden, x.sub_orden, x.id AS alerta_id, x.tipo,
         x.tipo IN ('error_escritura','rol_mal_impreso','contradiccion') AS error_del_aviso,
         x.texto, x.cita, x.origen, x.visto, a.rol, a.anio, a.tribunal,
         pi.ruta AS ruta_inicio, CASE WHEN pf.id <> pi.id THEN pf.ruta END AS ruta_fin
  FROM alertas x
  JOIN avisos a ON a.id = x.aviso_id
  JOIN ediciones e ON e.id = a.edicion_id
  LEFT JOIN paginas pi ON pi.id = a.pagina_inicio_id
  LEFT JOIN paginas pf ON pf.id = a.pagina_fin_id
  WHERE a.filtro_estado <> 'descartado';

-- Calendario. Un renglón por remate agendado, con los datos de su publicación visible más reciente.
DROP VIEW IF EXISTS v_calendario;
CREATE VIEW v_calendario AS
  SELECT g.id AS agenda_id, g.bien_id, b.inmueble, a.rol, a.anio, a.tribunal,
         e.fecha AS edicion_vigente, r.id AS remate_id, a.id AS aviso_id, a.orden,
         r.fecha_remate, r.hora_remate, r.modalidad, r.plataforma, r.direccion, r.comuna,
         r.minimo_monto, r.minimo_moneda, r.minimo_costas_clp,
         r.garantia_porcentaje, r.garantia_base, r.garantia_monto, r.garantia_moneda,
         r.vv_regla_texto, r.vv_desde, r.vv_desde_origen, r.vv_hasta, r.vv_estado,
         g.vv_entregado, g.remate_asistido, g.notas,
         (g.vv_entregado = 0 AND r.vv_hasta IS NOT NULL) AS mostrar_ventana_vv,   -- 0 cuando ya se entregó o no hay fecha
         pi.ruta AS ruta_inicio, CASE WHEN pf.id <> pi.id THEN pf.ruta END AS ruta_fin,
         (SELECT COUNT(*) FROM cambios k WHERE k.bien_id = g.bien_id AND k.visto = 0) AS cambios_sin_ver,
         (SELECT COUNT(*) FROM alertas x WHERE x.aviso_id = a.id AND x.sub_orden IN (0, r.sub_orden)) AS n_alertas
  FROM agenda g
  JOIN bienes b ON b.id = g.bien_id
  JOIN remates r ON r.id = (SELECT r2.id FROM remates r2
                            JOIN avisos a2 ON a2.id = r2.aviso_id
                            JOIN ediciones e2 ON e2.id = a2.edicion_id
                            WHERE r2.bien_id = g.bien_id AND a2.filtro_estado <> 'descartado'
                            ORDER BY e2.fecha DESC, r2.id DESC LIMIT 1)
  JOIN avisos a ON a.id = r.aviso_id
  JOIN ediciones e ON e.id = a.edicion_id
  LEFT JOIN paginas pi ON pi.id = a.pagina_inicio_id
  LEFT JOIN paginas pf ON pf.id = a.pagina_fin_id;

-- Visitas al tribunal para dejar vales vista (idea de Diego del 15 de Octubre). Solo los vales vista PENDIENTES.
-- Al marcar vv_entregado el remate sale de aquí. Los remates sin fecha de vale vista no entran y llevan alerta dato_faltante.
-- PROVISORIO. Hoy agrupa por tribunal y día del plazo final. La forma de agrupar con ventanas de varios días está por decidir con Diego.
DROP VIEW IF EXISTS v_entregas_vv;
CREATE VIEW v_entregas_vv AS
  SELECT tribunal, substr(vv_hasta, 1, 10) AS dia,
         MIN(CASE WHEN length(vv_hasta) > 10 THEN substr(vv_hasta, 12, 5) END) AS hora_limite,
         COUNT(*) AS vales_vista,
         MIN(vv_desde) AS desde_mas_temprano,
         group_concat(DISTINCT rol || '-' || anio) AS roles,
         group_concat(agenda_id) AS agenda_ids,
         MAX(vv_estado = 'revisar') AS hay_que_revisar,
         SUM(cambios_sin_ver) AS cambios_sin_ver
  FROM v_calendario
  WHERE vv_hasta IS NOT NULL AND vv_entregado = 0
  GROUP BY tribunal, substr(vv_hasta, 1, 10);

-- Historial de cada tribunal. Solo sirve como alarma cuando un aviso dice algo distinto, nunca como regla.
-- Cuenta avisos, no remates (el aviso 30 con 4 lotes cuenta una vez).
DROP VIEW IF EXISTS v_historial_tribunal;
CREATE VIEW v_historial_tribunal AS
  SELECT a.tribunal, r.vv_regla, COUNT(DISTINCT a.id) AS veces, MAX(e.fecha) AS ultima_vez
  FROM remates r
  JOIN avisos a ON a.id = r.aviso_id
  JOIN ediciones e ON e.id = a.edicion_id
  WHERE a.filtro_estado <> 'descartado' AND a.tribunal IS NOT NULL AND r.vv_regla IS NOT NULL
  GROUP BY a.tribunal, r.vv_regla;
