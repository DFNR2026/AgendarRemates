"""Lectura diaria en la nube (servidor/diario.py, 20 de Octubre). Sin internet, sin Supabase de verdad y sin Haiku.
Correr desde D:\\Agendar_Remates con. python -m pruebas.test_servidor
Trabaja sobre una copia en una carpeta temporal (capturas y ia_respuestas de mentira), así que no toca las del proyecto.
Lo esperado de cada caso se fijó antes de correr la prueba, a partir del diseño de la bitácora del 20 (puntos 3 a 5).
"""
import io, json, re, shutil, sys, tempfile, zipfile
from datetime import datetime
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from servidor import diario as D

FALLAS = []
def revisar(nombre, condicion, detalle=""):
    print(("OK    " if condicion else "FALLA ") + nombre, detalle)
    if not condicion: FALLAS.append(nombre)

antes_ia = sorted(p.name for p in (RAIZ / "ia_respuestas").rglob("*.json"))
antes_cap = sorted(p.name for p in (RAIZ / "capturas").iterdir())


class Supa:
    """Supabase de mentira, en memoria."""
    def __init__(self, archivos=None):
        self.a = dict(archivos or {})
    def existe(self, r): return r in self.a
    def leer_texto(self, r): return self.a[r].decode("utf-8")
    def bajar(self, r, local): Path(local).write_bytes(self.a[r])
    def subir(self, local, r, tipo="x"): self.a[r] = Path(local).read_bytes()
    def subir_texto(self, t, r): self.a[r] = t.encode("utf-8")
    def marca(self, r): return json.loads(self.a[r]) if r in self.a else None


tmp = Path(tempfile.mkdtemp())
D.RAIZ, D.CAPTURAS, D.CARPETA_IA = tmp, tmp / "capturas", tmp / "ia_respuestas"
(tmp / "ia_respuestas" / "vale_vista").mkdir(parents=True)
(tmp / "ia_respuestas" / "vale_vista" / "uno.json").write_text("{}", encoding="utf-8")
F = "2026-10-18"
AHORA = datetime(2026, 10, 18, 6, 50)


def lector(cuerpos, paginas=1, alarmas=()):
    """Lector de mentira. Escribe navegacion.json como el de verdad."""
    def leer(fecha):
        c = D.CAPTURAS / fecha
        shutil.rmtree(c, ignore_errors=True); c.mkdir(parents=True)
        (c / "F08_x.txt").write_text("texto", encoding="utf-8")
        nav = {"fecha": fecha, "cuerpos": cuerpos, "paginas_con_remates": [{"pagina": "F8"}] * paginas,
               "alarmas": list(alarmas)}
        (c / "navegacion.json").write_text(json.dumps(nav), encoding="utf-8")
        leer.llamado = True
        return 0
    leer.llamado = False
    return leer

DEL_DIA = {"F": "2026/10/18 n=16"}
OTRO_DIA = {"F": "2026/10/17 n=16"}


SERIE = [0]
def carga(sin_ia=0, nuevas=0):
    def cargar(fecha):
        for k in range(nuevas):
            (D.CARPETA_IA / "direccion").mkdir(exist_ok=True)
            (D.CARPETA_IA / "direccion" / f"n{SERIE[0]}.json").write_text("{}", encoding="utf-8")
            SERIE[0] += 1
        return {"avisos": 144, "remates": 147, "vale_vista": {"leidos": 127 - sin_ia, "sin_ia": sin_ia, "colores": {}},
                "direccion": {"leidos": 127, "sin_ia": 0, "colores": {}}}
    return cargar

def nada(fecha):
    raise AssertionError("no debía cargar")

# 1. Con marca no se hace nada
S = Supa({f"marcas/{F}.json": b"{}"}); L = lector(DEL_DIA)
revisar("con marca no lee el diario", D.correr(S, F, "real", False, AHORA, L, nada) == 0 and not L.llamado)

# 2 y 3. Edición todavía no publicada
S = Supa()
r = D.correr(S, F, "real", False, AHORA, lector(OTRO_DIA), nada)
revisar("edición no publicada y no es el último. sale con 2 y sin marca", r == 2 and S.marca(f"marcas/{F}.json") is None)
revisar("contador de intentos en 1", S.a[f"intentos/{F}.txt"] == b"1")
r = D.correr(S, F, "real", True, AHORA, lector(OTRO_DIA), nada)
m = S.marca(f"marcas/{F}.json") or {}
revisar("edición no publicada en el último intento. marca fallida con el motivo", r == 0 and m.get("estado") == "fallida"
        and "no tiene publicada" in (m.get("motivo") or ""), str(m))
revisar("contador de intentos en 2 y la marca lo dice", S.a[f"intentos/{F}.txt"] == b"2" and m.get("intentos") == 2)
revisar("fallida no sube captura", f"capturas/{F}.zip" not in S.a)
r = D.correr(Supa(), F, "real", False, AHORA, lector({}), nada)
revisar("sin ningún cuerpo tampoco cuenta como leída", r == 2)

# 4. Diario leído sin la sección de remates
S = Supa()
revisar("sin remates y no es el último. sale con 2", D.correr(S, F, "real", False, AHORA, lector(DEL_DIA, 0), nada) == 2
        and S.marca(f"marcas/{F}.json") is None)
D.correr(S, F, "real", True, AHORA, lector(DEL_DIA, 0), nada)
revisar("sin remates en el último intento. marca sin_remates y sube la captura",
        (S.marca(f"marcas/{F}.json") or {}).get("estado") == "sin_remates" and f"capturas/{F}.zip" in S.a)

# 5. Todo bien
S = Supa()
r = D.correr(S, F, "real", False, AHORA, lector(DEL_DIA, 8), carga(nuevas=2))
m = S.marca(f"marcas/{F}.json") or {}
revisar("lectura completa. marca listo con el resumen", r == 0 and m.get("estado") == "listo" and m.get("avisos") == 144
        and m.get("respuestas_nuevas") == 2 and m.get("paginas") == 8, str(m))
z = zipfile.ZipFile(io.BytesIO(S.a[f"capturas/{F}.zip"]))
revisar("la captura sube con su ruta capturas/AAAA-MM-DD", sorted(z.namelist()) == [f"capturas/{F}/F08_x.txt", f"capturas/{F}/navegacion.json"], str(z.namelist()))
zi = zipfile.ZipFile(io.BytesIO(S.a["estado/ia_respuestas.zip"]))
revisar("las respuestas suben todas, las viejas y las nuevas", sorted(zi.namelist()) == ["ia_respuestas/direccion/n0.json",
        "ia_respuestas/direccion/n1.json", "ia_respuestas/vale_vista/uno.json"], str(zi.namelist()))

# 6. Las respuestas de Supabase se juntan con las de git antes de leer
shutil.rmtree(D.CARPETA_IA / "direccion")
S2 = Supa({"estado/ia_respuestas.zip": S.a["estado/ia_respuestas.zip"]})
D.correr(S2, "2026-10-19", "real", False, AHORA, lector({"F": "2026/10/19 n=16"}, 8), carga())
revisar("baja las respuestas de Supabase antes de leer", (D.CARPETA_IA / "direccion" / "n1.json").exists())
revisar("sin respuestas nuevas no vuelve a subir el zip", S2.a["estado/ia_respuestas.zip"] == S.a["estado/ia_respuestas.zip"])

# 7. Haiku no respondió todo
S = Supa()
r = D.correr(S, F, "real", False, AHORA, lector(DEL_DIA, 8), carga(sin_ia=3, nuevas=1))
revisar("Haiku incompleto y no es el último. sale con 2, guarda lo ganado y sin marca",
        r == 2 and "estado/ia_respuestas.zip" in S.a and S.marca(f"marcas/{F}.json") is None)
D.correr(S, F, "real", True, AHORA, lector(DEL_DIA, 8), carga(sin_ia=3))
m = S.marca(f"marcas/{F}.json") or {}
revisar("Haiku incompleto en el último intento. marca incompleta con el motivo", m.get("estado") == "incompleta"
        and "3 lecturas" in (m.get("motivo") or ""), str(m))

# 8. Páginas que no se pudieron leer
S = Supa()
revisar("páginas fallidas y no es el último. sale con 2",
        D.correr(S, F, "real", False, AHORA, lector(DEL_DIA, 8, ["No se pudo leer F9 (x). error"]), nada) == 2)
D.correr(S, F, "real", True, AHORA, lector(DEL_DIA, 8, ["No se pudo leer F9 (x). error"]), carga())
revisar("páginas fallidas en el último intento. marca incompleta", (S.marca(f"marcas/{F}.json") or {}).get("estado") == "incompleta")

# 9. Modo ensayo
S = Supa({f"marcas/{F}.json": b"{}"})
D.correr(S, F, "ensayo", False, AHORA, lector(DEL_DIA, 8), carga())
revisar("ensayo no mira la marca real y guarda en pruebas/ensayo", (S.marca(f"pruebas/ensayo/marcas/{F}.json") or {}).get("estado") == "listo"
        and S.a[f"marcas/{F}.json"] == b"{}" and f"pruebas/ensayo/capturas/{F}.zip" in S.a)

# 10. Lector con error
S = Supa()
revisar("lector con error y no es el último. sale con 2", D.correr(S, F, "real", False, AHORA, lambda f: 1, nada) == 2)

# 11. Último intento por la hora
revisar("8:29 no es el último intento", not D.es_final(datetime(2026, 10, 18, 8, 29), ""))
revisar("8:30 sí es el último intento", D.es_final(datetime(2026, 10, 18, 8, 30), ""))
revisar("a mano siempre es el último", D.es_final(datetime(2026, 10, 18, 6, 0), "1"))

# 12. La captura de verdad del 18 de Octubre pasa la revisión
D.CAPTURAS = RAIZ / "capturas"
rv = D.revisar_captura(F)
revisar("captura real del 18 de Octubre. sin problemas y 8 páginas de remates", rv["problema"] is None and rv["paginas"] == 8, str(rv))
D.CAPTURAS = tmp / "capturas"

# 13. Horarios del flujo. Los 7 intentos de 6:30 a 8:35 en verano (UTC-3) y en invierno (UTC-4)
yml = (RAIZ / ".github" / "workflows" / "diario.yml").read_text(encoding="utf-8")
utc = set()
for minutos, horas in re.findall(r'cron: "([\d,]+) ([\d,]+) \* \* \*"', yml):
    utc |= {(int(h), int(m)) for h in horas.split(",") for m in minutos.split(",")}
QUIERO = [(6, 30), (6, 50), (7, 10), (7, 30), (7, 50), (8, 10), (8, 35)]
for nombre, desfase in (("verano", 3), ("invierno", 4)):
    chile = {((h - desfase) % 24, m) for h, m in utc}
    revisar(f"horario de GitHub cubre los 7 intentos en {nombre}", all(x in chile for x in QUIERO), str(sorted(chile)))
revisar("ventana del flujo de 6:25 a 8:40", '-lt 0625' in yml and '-gt 0840' in yml)

shutil.rmtree(tmp, ignore_errors=True)
revisar("candado. ia_respuestas del proyecto sin cambios (no llamó a Haiku)",
        antes_ia == sorted(p.name for p in (RAIZ / "ia_respuestas").rglob("*.json")))
revisar("capturas del proyecto sin cambios", antes_cap == sorted(p.name for p in (RAIZ / "capturas").iterdir()))
print("\nRESULTADO.", "TODO OK" if not FALLAS else f"{len(FALLAS)} fallas")
sys.exit(1 if FALLAS else 0)
