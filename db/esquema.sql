-- Esquema de la base de Agendar_Remates (SQLite). Versión 1, 2026-10-14.
-- Siete cajones aprobados por Diego. Ediciones, Páginas, Avisos, Citas, Causas (con su registro de cambios), Mi agenda, Feriados.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS meta (
  clave TEXT PRIMARY KEY,
  valor TEXT NOT NULL
);

-- 1. EDICIONES. Un registro por diario leído.
CREATE TABLE IF NOT EXISTS ediciones (
  id               INTEGER PRIMARY KEY,
  fecha            TEXT NOT NULL UNIQUE,            -- AAAA-MM-DD de la edición
  leida_en         TEXT NOT NULL,                   -- fecha y hora de la lectura
  estado           TEXT NOT NULL CHECK (estado IN ('ok','con_alarmas','fallida')),
  cuerpos_revisados TEXT,                           -- ej. "A8 B12 C12"
  roles_en_texto   INTEGER,                         -- roles que el código contó en el texto
  avisos_extraidos INTEGER,                         -- avisos que quedaron en la base (deben cuadrar)
  alarmas          TEXT                             -- una alarma por línea, vacío si cuadró todo
);

-- 2. PÁGINAS. La evidencia. Texto completo de cada página con remates.
CREATE TABLE IF NOT EXISTS paginas (
  id            INTEGER PRIMARY KEY,
  edicion_id    INTEGER NOT NULL REFERENCES ediciones(id) ON DELETE CASCADE,
  cuerpo        TEXT NOT NULL,                      -- B, C, D, F, G...
  numero        INTEGER NOT NULL,                   -- número de página dentro del cuerpo
  id_pagina     TEXT NOT NULL,                      -- código del visor (no se asume formato)
  orden_rollo   INTEGER,                            -- posición en el rollo unido
  cornisas_1616 INTEGER NOT NULL DEFAULT 0,
  flechas       TEXT,                               -- "MÁS AVISOS..." y "VIENEN DE..." encontradas
  texto         TEXT NOT NULL,
  sha256        TEXT NOT NULL,
  UNIQUE (edicion_id, cuerpo, numero)
);

-- 5. CAUSAS. Une todas las publicaciones de un mismo remate.
CREATE TABLE IF NOT EXISTS causas (
  id          INTEGER PRIMARY KEY,
  clave       TEXT NOT NULL UNIQUE,                 -- rol-año|tribunal normalizado (misma llave del Mercurio)
  tipo_id     TEXT NOT NULL CHECK (tipo_id IN ('ROL','RIT')),
  rol         TEXT NOT NULL,                        -- solo dígitos
  anio        TEXT NOT NULL,
  tribunal    TEXT NOT NULL,
  corte       TEXT
);

-- 3. AVISOS. Una fila por publicación de un aviso en una edición.
CREATE TABLE IF NOT EXISTS avisos (
  id                  INTEGER PRIMARY KEY,
  edicion_id          INTEGER NOT NULL REFERENCES ediciones(id) ON DELETE CASCADE,
  causa_id            INTEGER REFERENCES causas(id),   -- NULL si el aviso no trae rol ni RIT
  orden               INTEGER NOT NULL,                -- posición del aviso en el rollo
  pagina_inicio       TEXT,                            -- ej. "B11"
  pagina_fin          TEXT,                            -- distinta de la de inicio si el aviso va partido
  texto               TEXT NOT NULL,                   -- texto completo del aviso
  rol_impreso         TEXT,                            -- tal como viene en el diario (C-39902025, CC-936-2026...)
  tipo_id             TEXT CHECK (tipo_id IN ('ROL','RIT','SIN_ROL')),
  rol                 TEXT,
  anio                TEXT,
  tribunal            TEXT,
  corte               TEXT,
  demandante          TEXT,
  demandado           TEXT,
  direccion           TEXT,
  comuna              TEXT,
  fojas               TEXT,
  anio_dominio        INTEGER,
  fecha_remate        TEXT,                            -- AAAA-MM-DD
  hora_remate         TEXT,                            -- HH:MM
  modalidad           TEXT CHECK (modalidad IN ('zoom','presencial','mixta','sin_dato')),
  minimo_monto        REAL,
  minimo_moneda       TEXT CHECK (minimo_moneda IN ('CLP','UF')),
  garantia_porcentaje REAL,                            -- ej. 10 si dice "10% del mínimo"
  garantia_monto      REAL,                            -- si el aviso da un monto fijo
  garantia_moneda     TEXT CHECK (garantia_moneda IN ('CLP','UF')),
  vv_regla_texto      TEXT,                            -- regla del vale vista con las palabras del aviso
  vv_desde            TEXT,                            -- AAAA-MM-DD HH:MM calculado por código
  vv_hasta            TEXT,
  vv_estado           TEXT CHECK (vv_estado IN ('calculado','revisar','sin_dato')),
  filtro_estado       TEXT NOT NULL DEFAULT 'pasa' CHECK (filtro_estado IN ('pasa','fuera_filtro')),
  filtro_motivos      TEXT,                            -- ej. "BancoEstado; dominio 2022"
  verificacion        TEXT NOT NULL DEFAULT 'pendiente' CHECK (verificacion IN ('completa','con_rojos','pendiente')),
  UNIQUE (edicion_id, orden)
);
CREATE INDEX IF NOT EXISTS ix_avisos_rol ON avisos(rol, anio);
CREATE INDEX IF NOT EXISTS ix_avisos_tribunal ON avisos(tribunal);
CREATE INDEX IF NOT EXISTS ix_avisos_causa ON avisos(causa_id);

-- 4. CITAS. El candado contra datos inventados. Una fila por dato extraído.
CREATE TABLE IF NOT EXISTS citas (
  id          INTEGER PRIMARY KEY,
  aviso_id    INTEGER NOT NULL REFERENCES avisos(id) ON DELETE CASCADE,
  campo       TEXT NOT NULL,                        -- nombre de la columna de avisos
  valor       TEXT,
  cita        TEXT,                                 -- frase exacta del diario
  metodo      TEXT NOT NULL CHECK (metodo IN ('codigo','ia')),
  verificada  INTEGER NOT NULL CHECK (verificada IN (0,1)),  -- 1 si el código encontró la cita en el texto del aviso
  UNIQUE (aviso_id, campo)
);

-- 5b. CAMBIOS ENTRE PUBLICACIONES de una misma causa (parte del cajón Causas).
CREATE TABLE IF NOT EXISTS cambios (
  id               INTEGER PRIMARY KEY,
  causa_id         INTEGER NOT NULL REFERENCES causas(id) ON DELETE CASCADE,
  aviso_anterior   INTEGER NOT NULL REFERENCES avisos(id),
  aviso_nuevo      INTEGER NOT NULL REFERENCES avisos(id),
  campo            TEXT NOT NULL,
  valor_anterior   TEXT,
  valor_nuevo      TEXT,
  detectado_en     TEXT NOT NULL,
  visto            INTEGER NOT NULL DEFAULT 0
);

-- 6. MI AGENDA. Los remates que Diego elige. Quitar del calendario = borrar la fila (botón X).
CREATE TABLE IF NOT EXISTS agenda (
  id              INTEGER PRIMARY KEY,
  causa_id        INTEGER NOT NULL UNIQUE REFERENCES causas(id),
  aviso_base_id   INTEGER NOT NULL REFERENCES avisos(id),  -- publicación vigente cuando se agendó
  agregado_en     TEXT NOT NULL,
  vv_entregado    INTEGER NOT NULL DEFAULT 0,               -- casilla opcional
  remate_asistido INTEGER NOT NULL DEFAULT 0,               -- casilla opcional
  notas           TEXT
);

-- 7. FERIADOS. Para calcular reglas como "el viernes anterior, o el día hábil anterior si es feriado".
CREATE TABLE IF NOT EXISTS feriados (
  fecha   TEXT PRIMARY KEY,                         -- AAAA-MM-DD
  nombre  TEXT NOT NULL,
  ambito  TEXT NOT NULL CHECK (ambito IN ('nacional','regional')),
  fuente  TEXT NOT NULL
);

-- Vista. Lo que se sabe de cada tribunal, calculado desde sus avisos. Solo sirve como alarma, nunca como regla.
CREATE VIEW IF NOT EXISTS v_historial_tribunal AS
  SELECT tribunal, vv_regla_texto, COUNT(*) AS veces, MAX(e.fecha) AS ultima_vez
  FROM avisos a JOIN ediciones e ON e.id = a.edicion_id
  WHERE tribunal IS NOT NULL AND vv_regla_texto IS NOT NULL
  GROUP BY tribunal, vv_regla_texto;

-- Vista. Lo que alimenta el calendario. Toma la publicación más reciente de cada causa agendada.
CREATE VIEW IF NOT EXISTS v_calendario AS
  SELECT ag.id AS agenda_id, c.rol, c.anio, c.tribunal,
         a.fecha_remate, a.hora_remate, a.modalidad, a.vv_desde, a.vv_hasta, a.vv_estado,
         a.minimo_monto, a.minimo_moneda, a.garantia_porcentaje, a.garantia_monto, a.garantia_moneda,
         ag.vv_entregado, ag.remate_asistido, ag.notas,
         (SELECT COUNT(*) FROM cambios k WHERE k.causa_id = c.id AND k.visto = 0) AS cambios_sin_ver
  FROM agenda ag
  JOIN causas c ON c.id = ag.causa_id
  JOIN avisos a ON a.id = (SELECT a2.id FROM avisos a2 JOIN ediciones e2 ON e2.id = a2.edicion_id
                           WHERE a2.causa_id = c.id ORDER BY e2.fecha DESC, a2.id DESC LIMIT 1);
