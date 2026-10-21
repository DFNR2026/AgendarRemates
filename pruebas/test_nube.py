"""Mitad del PC del lector diario (interfaz/nube.py, 20 de Octubre). Sin internet, sin Supabase de verdad y sin Haiku.
Correr desde D:\\Agendar_Remates con. python -m pruebas.test_nube
Trabaja en una carpeta temporal con una copia de interfaz_prueba_antes_18oct.db (ediciones hasta el 17 de Octubre).
Referencia fijada antes. La edición del 18 de Octubre bajada de la "nube" debe quedar aviso por aviso igual a la que Diego
cargó con Haiku el 20 de Octubre en interfaz_prueba.db (bitácora del 18, punto 64).
"""
import io, json, shutil, sqlite3, sys, tempfile, zipfile
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from interfaz import nube as N

FALLAS = []
def revisar(nombre, condicion, detalle=""):
    print(("OK    " if condicion else "FALLA ") + nombre, detalle)
    if not condicion: FALLAS.append(nombre)

antes_ia = sorted(p.name for p in (RAIZ / "ia_respuestas").rglob("*.json"))
antes_cap = sorted(p.name for p in (RAIZ / "capturas").iterdir())
REAL_DEL_PROYECTO = RAIZ / "agendar_remates.db"
real_antes = REAL_DEL_PROYECTO.stat().st_mtime if REAL_DEL_PROYECTO.exists() else None


def zip_de(carpeta: Path, base: Path, solo=None) -> bytes:
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        for p in sorted(carpeta.rglob("*")):
            if p.is_file() and (solo is None or p.name in solo):
                z.write(p, p.relative_to(base).as_posix())
    return b.getvalue()


class Supa:
    def __init__(self, a): self.a = a; self.bajadas = []
    def existe(self, r): return r in self.a
    def leer_texto(self, r): return self.a[r].decode("utf-8")
    def bajar(self, r, local): self.bajadas.append(r); Path(local).write_bytes(self.a[r])
    def listar(self, pref): return [k[len(pref):] for k in self.a if k.startswith(pref)]


tmp = Path(tempfile.mkdtemp())
# El candado se prueba contra una base "real" de mentira en la carpeta temporal. Así, aunque el candado se rompa, la prueba
# nunca abre agendar_remates.db (corrección del 20 de Octubre, una mutación del candado alcanzó a abrirla, sin cargar nada).
BASE_REAL = tmp / "agendar_remates_de_mentira.db"
base = tmp / "prueba.db"
shutil.copy(RAIZ / "interfaz_prueba_antes_18oct.db", base)
uno_ia = sorted((RAIZ / "ia_respuestas" / "vale_vista").glob("*.json"))[0].name
S = Supa({
    "marcas/2026-10-18.json": json.dumps({"fecha": "2026-10-18", "estado": "listo"}).encode(),
    "marcas/2026-10-19.json": json.dumps({"fecha": "2026-10-19", "estado": "fallida",
                                          "motivo": "El diario todavía no tiene publicada la edición de esta fecha."}).encode(),
    "marcas/2026-09-01.json": json.dumps({"fecha": "2026-09-01", "estado": "listo"}).encode(),
    "capturas/2026-10-18.zip": zip_de(RAIZ / "capturas" / "2026-10-18", RAIZ),
    "estado/ia_respuestas.zip": zip_de(RAIZ / "ia_respuestas", RAIZ, {uno_ia}),
})
CONF = {"url": "x", "clave": "x", "aprobada": False}

r = N.actualizar(base, "2026-10-19", S, raiz=tmp, base_real=BASE_REAL, conf=CONF)
revisar("carga el 18 de Octubre que faltaba", r["ok"] and r["cargadas"] == ["2026-10-18"], str(r))
revisar("la edición fallida del 19 no se carga y se avisa con su motivo", any("no pudo leer la edición del lunes 19 de Octubre" in p
        and "no tiene publicada" in p for p in r["problemas"]), str(r["problemas"]))
revisar("la marca de más de 30 días atrás no se mira", "capturas/2026-09-01.zip" not in S.bajadas)
revisar("la captura bajada queda en capturas/2026-10-18", (tmp / "capturas" / "2026-10-18" / "navegacion.json").exists())
revisar("las respuestas de la nube se juntan en ia_respuestas", (tmp / "ia_respuestas" / "vale_vista" / uno_ia).exists())

c = sqlite3.connect(base); ref = sqlite3.connect(RAIZ / "interfaz_prueba.db")
Q = ("SELECT a.orden, r.sub_orden, r.vv_estado, r.vv_desde, r.vv_hasta, r.vv_regla, r.direccion, r.comuna, r.fecha_remate "
     "FROM remates r JOIN avisos a ON a.id = r.aviso_id JOIN ediciones e ON e.id = a.edicion_id WHERE e.fecha = '2026-10-18' ORDER BY 1, 2")
nuevo, viejo = c.execute(Q).fetchall(), ref.execute(Q).fetchall()
revisar("147 remates del 18 de Octubre", len(nuevo) == 147, str(len(nuevo)))
revisar("vale vista, dirección y fecha iguales aviso por aviso a la carga con Haiku del 20 de Octubre", nuevo == viejo,
        str([x for x in zip(nuevo, viejo) if x[0] != x[1]][:2]))
QA = ("SELECT a.orden, al.tipo, al.texto FROM alertas al JOIN avisos a ON a.id = al.aviso_id JOIN ediciones e ON e.id = a.edicion_id "
      "WHERE e.fecha = '2026-10-18' ORDER BY 1, 2, 3")
revisar("alertas del 18 iguales a la carga con Haiku", c.execute(QA).fetchall() == ref.execute(QA).fetchall())
# CORRECCIÓN del 21 de Octubre. Antes se comparaba el total de cambios de las dos bases, y eso dependía de lo cargado antes del 18
# en interfaz_prueba.db (que se rehízo con el descarte de tribunales no civiles y pasó de 8 a 7). Ahora se comparan solo los
# cambios que nacen con la edición del 18 de Octubre, que es lo que esta prueba carga.
QC = ("SELECT k.campo, k.valor_anterior, k.valor_nuevo FROM cambios k JOIN remates r ON r.id = k.remate_nuevo JOIN avisos a ON a.id = r.aviso_id "
      "JOIN ediciones e ON e.id = a.edicion_id WHERE e.fecha = '2026-10-18' ORDER BY 1, 2, 3")
revisar("cambios que nacen con el 18 de Octubre iguales a la carga con Haiku", c.execute(QC).fetchall() == ref.execute(QC).fetchall(),
        f"{c.execute(QC).fetchall()} {ref.execute(QC).fetchall()}")
ref.close()

r = N.actualizar(base, "2026-10-19", S, raiz=tmp, base_real=BASE_REAL, conf=CONF)
revisar("segunda vez no carga nada de nuevo", r["ok"] and r["cargadas"] == [] and r["retomadas"] == [], str(r))

# Retomar. Una edición local incompleta cuya marca ya dice listo se termina con lo guardado. Se usa el 15 de Octubre, que en la
# base original está completo (estado ok). El 17 no sirve, porque de verdad le faltan lecturas de Haiku (3 de 123).
c.execute("UPDATE ediciones SET estado = 'con_alarmas', alarmas = 'Vale vista. 1 de 99 avisos quedaron sin leer por la IA. "
          "Se puede retomar sin volver a leer el Mercurio.' WHERE fecha = '2026-10-15'"); c.commit()
S.a["marcas/2026-10-15.json"] = json.dumps({"fecha": "2026-10-15", "estado": "listo"}).encode()
r = N.actualizar(base, "2026-10-19", S, raiz=tmp, base_real=BASE_REAL, conf=CONF)
al = c.execute("SELECT alarmas FROM ediciones WHERE fecha = '2026-10-15'").fetchone()[0]
revisar("edición incompleta con marca listo se retoma y queda sin la alarma del vale vista", r["retomadas"] == ["2026-10-15"]
        and not (al or "").startswith("Vale vista."), str(r) + " " + str(al))
c.close()

# Errores y candados
class Caida(Supa):
    def listar(self, pref): raise OSError("[Errno 11001] getaddrinfo failed")
r = N.actualizar(base, "2026-10-19", Caida({}), raiz=tmp, base_real=BASE_REAL, conf=CONF)
revisar("sin internet no se cae y lo dice en palabras simples", not r["ok"] and "internet" in (r["error"] or ""), str(r))
r = N.actualizar(base, "2026-10-19", None, raiz=tmp, base_real=BASE_REAL, conf={})
revisar("sin la clave de Supabase en config.py lo dice", not r["ok"] and "config.py" in (r["error"] or ""), str(r))
r = N.actualizar(BASE_REAL, "2026-10-19", S, raiz=tmp, base_real=BASE_REAL, conf=CONF)
revisar("candado de la base real. sin aprobación no carga y lo explica", r["bloqueo"] and not r["cargadas"], str(r))
revisar("la base real de mentira ni siquiera se creó", not BASE_REAL.exists())

shutil.rmtree(tmp, ignore_errors=True)
revisar("candado. ia_respuestas del proyecto sin cambios (no llamó a Haiku)",
        antes_ia == sorted(p.name for p in (RAIZ / "ia_respuestas").rglob("*.json")))
revisar("capturas del proyecto sin cambios", antes_cap == sorted(p.name for p in (RAIZ / "capturas").iterdir()))
revisar("agendar_remates.db del proyecto no se tocó", (REAL_DEL_PROYECTO.stat().st_mtime if REAL_DEL_PROYECTO.exists() else None) == real_antes)
print("\nRESULTADO.", "TODO OK" if not FALLAS else f"{len(FALLAS)} fallas")
sys.exit(1 if FALLAS else 0)
