"""Carga el banco nivel 2 del 14 de Octubre en una base (parte 3.5, etapa 2).
Uso. python -m db.cargar_banco RUTA_BASE   (desde D:\\Agendar_Remates). No usar con la base real.
El texto de los avisos sale del cortador y los datos del banco_nivel2_2026-10-14.json.
"""
import json, re, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor.cortador import construir_rollo, cortar, roles_en
from motor.orden_columnas import leer_pagina
from db.carga import guardar_edicion

B = RAIZ / "banco_pruebas" / "2026-10-14"
# Códigos del visor de las dos páginas (capturas/2026-10-14/navegacion.json e inventario_correcto_2026-10-14.json)
PAGINAS = [("B11", "B", 11, "B-20261014-011"), ("C8", "C", 8, "L64MFDBT")]

# Las dudas del banco las escribió Claude al anotar. Esta clasificación las convierte en alertas para probar la base.
# El orden importa. La primera regla que calza decide.
REGLAS_DUDAS = [
    (None, r"fuera de filtro|Iba pegado|Evidencia para día hábil|Tribunal de cobranza|RIT laboral|^Juez partidor|Cae en día hábil a la misma hora|Es un solo remate|sin fecha de entrega"),   # la última la cubre el código (dato_faltante)
    ("contradiccion", r"[Cc]ontradic"),
    ("rol_mal_impreso", r"Rol impreso"),
    ("error_escritura", r"errata del diario"),
    ("condicion_especial", r"20%|TASACIÓN|no dice porcentaje|remite a las bases|No usa vale vista|mismo remate|días antes|martes o jueves|"
                           r"cupón de pago|Google Meet|vendaya|DOS remates|CUATRO remates|primer llamado|Tercer llamado|sin fecha de entrega|"
                           r"carpeta electrónica|Si se suspende"),
    ("aviso_previo", r"correo|OJV"),
]


def clasificar_duda(texto: str):
    for tipo, patron in REGLAS_DUDAS:
        if re.search(patron, texto):
            return tipo
    return "revisar_lectura"


def datos_banco():
    paginas = [{"nombre": n, "cuerpo": c, "numero": k, "id_pagina": i, "orden_rollo": o,
                "texto": (B / f"mercurio_2026-10-14_{n}.txt").read_text(encoding="utf-8")}
               for o, (n, c, k, i) in enumerate(PAGINAS, start=1)]
    rollo, marcas = construir_rollo([(n, leer_pagina(B / f"mercurio_2026-10-14_{n}.txt")) for n, *_ in PAGINAS])
    avisos = cortar(rollo, marcas)
    banco = json.loads((B / "banco_nivel2_2026-10-14.json").read_text(encoding="utf-8"))["avisos"]
    edicion = {"fecha": "2026-10-14", "leida_en": "2026-10-15T00:14:24", "estado": "ok", "cuerpos_revisados": "A8 B12 C12",
               "roles_en_texto": len({(r[1], r[2]) for r in roles_en(rollo)})}
    return edicion, paginas, avisos, {a["n"]: a for a in banco}


def cargar(con, ahora="2026-10-15T00:00:00"):
    edicion, paginas, avisos, extraido = datos_banco()
    return guardar_edicion(con, edicion, paginas, avisos, extraido, ahora, clasificar_duda)


if __name__ == "__main__":
    from db.crear_base import crear, BASE
    ruta = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if ruta is None or ruta.resolve() == BASE.resolve():
        raise SystemExit("Indica una base de prueba. El banco no se carga en agendar_remates.db.")
    print(cargar(crear(ruta)))
