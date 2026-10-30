"""Lectura diaria de Agendar_Remates en GitHub Actions (20 de Octubre de 2026, diseño de Diego en la bitácora del 20).

La nube solo lee el diario y llama a Haiku. No toca ninguna base de Diego. Sube a Supabase (bucket "agendar") la captura
del día y las respuestas de Haiku, y deja una marca con el resumen. El PC de Diego baja eso al abrir la agenda.

Pasos.
1. Si ya hay marca de la edición (modo real), no hace nada.
2. Baja de Supabase estado/ia_respuestas.zip (las respuestas que la nube ya pagó) y las junta con las de git.
3. Lee la edición con motor.lector_mercurio, el mismo del PC.
4. Revisa que de verdad se hayan leído remates. El lector no se cae si la edición aún no está publicada, solo deja 0 páginas.
   Si no hay remates o fallaron páginas, y no es el último intento, sale sin marca para que el siguiente reintente.
5. Carga la edición en una base de paso (se bota al final) para que Haiku lea el vale vista y la dirección de los avisos
   sin respuesta guardada. Si Haiku no respondió todo y no es el último intento, guarda lo ganado y sale para reintentar.
6. Sube capturas/AAAA-MM-DD.zip, estado/ia_respuestas.zip y marcas/AAAA-MM-DD.json.

Estados de la marca. listo, incompleta (Haiku o páginas pendientes en el último intento), sin_remates (el diario se leyó
y no trae la sección) y fallida (en el último intento no se pudo leer la edición). Solo se escribe una marca al terminar
bien o en el último intento. Si hay marca no se vuelve a intentar, salvo que sea fallida (F2-05, 30 de Octubre).
7. En el último intento, después de la edición de hoy, revisa los 7 días anteriores y lee hasta 2 sin marca o con marca
   fallida (F2-05). Así un día que la nube no leyó no se pierde para siempre.

Variables de entorno. MODO real o ensayo (ensayo guarda en pruebas/ensayo/ y no mira la marca), FECHA AAAA-MM-DD (por
defecto hoy en Chile, el flujo fija TZ=America/Santiago), INTENTO_FINAL 1 para forzar el último intento,
SUPABASE_URL y SUPABASE_KEY.
Códigos de salida. 0 terminado, 2 reintentar más tarde, 1 error del programa.
"""
from __future__ import annotations
import json, os, shutil, subprocess, sys, tempfile, traceback, zipfile
from datetime import date, datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

ULTIMO_DESDE = (8, 30)     # desde esta hora de Chile el intento es el último (el último va a las 8:35)
CARPETA_IA = RAIZ / "ia_respuestas"
CAPTURAS = RAIZ / "capturas"
RECUPERAR_DIAS = 7     # días hacia atrás que revisa el último intento (F2-05, 30 de Octubre). Puesto por Claude.
RECUPERAR_MAX = 2      # máximo de días atrasados por corrida, porque el flujo tiene 30 minutos. Puesto por Claude.


def log(msg: str) -> None:
    print(f"[diario] {msg}", flush=True)


def es_final(ahora: datetime, forzado: str) -> bool:
    if forzado == "1":
        return True
    if forzado == "0":
        return False
    return (ahora.hour, ahora.minute) >= ULTIMO_DESDE


def contar_ia() -> int:
    return sum(1 for p in CARPETA_IA.rglob("*.json")) if CARPETA_IA.exists() else 0


def zip_carpeta(carpeta: Path, destino: Path, base: Path) -> None:
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(carpeta.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(base).as_posix())


def revisar_captura(fecha: str) -> dict:
    """Mira capturas/FECHA/navegacion.json. Devuelve {problema, sin_remates, paginas, alarmas}."""
    nav_p = CAPTURAS / fecha / "navegacion.json"
    if not nav_p.exists():
        return {"problema": "El lector no dejó navegacion.json.", "sin_remates": False, "paginas": 0, "alarmas": []}
    nav = json.loads(nav_p.read_text(encoding="utf-8"))
    alarmas = list(nav.get("alarmas") or [])
    cuerpos = nav.get("cuerpos") or {}
    d = fecha.replace("-", "/")
    del_dia = [s for s, v in cuerpos.items() if str(v).startswith(d)]
    paginas = len(nav.get("paginas_con_remates") or [])
    fallas = [a for a in alarmas if a.startswith("No se pudo leer")]
    if not del_dia:
        return {"problema": "El diario todavía no tiene publicada la edición de esta fecha.", "sin_remates": False,
                "paginas": 0, "alarmas": alarmas}
    if paginas == 0:
        return {"problema": "Se leyó el diario pero no apareció la sección 1616 Remates de propiedades.",
                "sin_remates": True, "paginas": 0, "alarmas": alarmas}
    if fallas:
        return {"problema": f"No se pudieron leer {len(fallas)} páginas del diario.", "sin_remates": False,
                "paginas": paginas, "alarmas": alarmas}
    return {"problema": None, "sin_remates": False, "paginas": paginas, "alarmas": alarmas}


def estado_marca(E, marca: str) -> str | None:
    """None si no hay marca. Si la hay, su estado ('?' si no se puede leer, y cuenta como hecha)."""
    if not E.existe(marca):
        return None
    try:
        return json.loads(E.leer_texto(marca)).get("estado") or "?"
    except Exception:
        return "?"


def leer_diario(fecha: str) -> int:
    """Corre el lector del PC tal cual. Devuelve su código de salida."""
    return subprocess.run([sys.executable, "-m", "motor.lector_mercurio", "--fecha", fecha], cwd=RAIZ).returncode


def cargar_con_haiku(fecha: str) -> dict:
    """Carga la edición en una base de paso solo para que Haiku lea lo que falta. La base se bota."""
    from db.crear_base import crear
    from motor.procesar_edicion import cargar_edicion, cliente_o_nada
    cliente, motivo = cliente_o_nada()
    if motivo:
        log(motivo)
    tmp = Path(tempfile.mkdtemp()) / "paso.db"
    try:
        con = crear(tmp)
        res = cargar_edicion(con, fecha, datetime.now().isoformat(timespec="seconds"), cliente=cliente, usar_ia=True)
        con.close()
        return res
    finally:
        shutil.rmtree(tmp.parent, ignore_errors=True)


def correr(E, fecha: str, modo: str, final: bool, ahora: datetime, leer=leer_diario, cargar=cargar_con_haiku) -> int:
    P = "" if modo == "real" else "pruebas/ensayo/"
    marca = f"{P}marcas/{fecha}.json"
    log(f"Edición {fecha}. Modo {modo}. Hora de Chile {ahora:%H:%M}. Último intento {'sí' if final else 'no'}.")
    if modo == "real":
        est = estado_marca(E, marca)
        if est == "fallida":       # F2-05 (30 de Octubre). Antes una marca fallida bloqueaba para siempre
            log("La marca de esta edición quedó fallida. Se vuelve a intentar.")
        elif est:
            log("Ya hay marca de esta edición. No se hace nada.")
            return 0
    cont_remoto = f"{P}intentos/{fecha}.txt"
    intentos = (int(E.leer_texto(cont_remoto).strip() or 0) if E.existe(cont_remoto) else 0) + 1
    E.subir_texto(str(intentos), cont_remoto)
    log(f"Intento número {intentos}.")

    if E.existe("estado/ia_respuestas.zip"):
        z = RAIZ / "_ia_respuestas.zip"
        E.bajar("estado/ia_respuestas.zip", z)
        with zipfile.ZipFile(z) as zz:
            zz.extractall(RAIZ)
        z.unlink()
    ia_antes = contar_ia()
    log(f"Respuestas de Haiku disponibles {ia_antes}.")

    def subir_ia():
        z = RAIZ / "_ia_respuestas.zip"
        zip_carpeta(CARPETA_IA, z, RAIZ)
        E.subir(z, "estado/ia_respuestas.zip", "application/zip")
        z.unlink()

    def subir_captura():
        z = RAIZ / f"_{fecha}.zip"
        zip_carpeta(CAPTURAS / fecha, z, RAIZ)
        E.subir(z, f"{P}capturas/{fecha}.zip", "application/zip")
        z.unlink()

    def poner_marca(estado: str, motivo: str | None, extra: dict | None = None):
        datos = {"fecha": fecha, "estado": estado, "motivo": motivo, "intentos": intentos,
                 "hora": ahora.isoformat(timespec="minutes"), "modo": modo} | (extra or {})
        E.subir_texto(json.dumps(datos, ensure_ascii=False, indent=1), marca)
        log(f"Marca {estado}. {motivo or ''}")

    codigo = leer(fecha)
    rev = revisar_captura(fecha) if codigo == 0 else {"problema": f"El lector terminó con error (código {codigo}).",
                                                       "sin_remates": False, "paginas": 0, "alarmas": []}
    log(f"Lectura. Código {codigo}. Páginas de remates {rev['paginas']}. {rev['problema'] or 'Sin problemas.'}")
    if rev["problema"] and rev["paginas"] == 0:
        if not final:
            log("Se reintenta en el próximo intento.")
            return 2
        if rev["sin_remates"]:
            subir_captura()
            poner_marca("sin_remates", rev["problema"], {"paginas": 0})
        else:
            poner_marca("fallida", rev["problema"])
        return 0
    if rev["problema"] and not final:
        log("Se reintenta en el próximo intento.")
        return 2

    res = cargar(fecha)
    vv, dr = res.get("vale_vista") or {}, res.get("direccion") or {}
    pend = (vv.get("sin_ia") or 0) + (dr.get("sin_ia") or 0)
    nuevas = contar_ia() - ia_antes
    resumen = {"paginas": rev["paginas"], "avisos": res.get("avisos"), "remates": res.get("remates"),
               "vale_vista": {k: vv.get(k) for k in ("leidos", "sin_ia", "colores")},
               "direccion": {k: dr.get(k) for k in ("leidos", "sin_ia", "colores")},
               "respuestas_nuevas": nuevas}
    log(f"Carga de paso. {resumen}")
    if nuevas:
        subir_ia()
    if pend and not final:
        log(f"Haiku dejó {pend} lecturas sin hacer. Se reintenta en el próximo intento.")
        return 2
    subir_captura()
    if rev["problema"] or pend:
        motivo = " ".join(x for x in (rev["problema"], f"Haiku dejó {pend} lecturas sin hacer." if pend else None) if x)
        poner_marca("incompleta", motivo, resumen)
    else:
        poner_marca("listo", None, resumen)
    return 0


def pendientes(E, hoy: str, dias: int = RECUPERAR_DIAS) -> list:
    """Días anteriores a hoy, del más nuevo al más viejo, sin marca o con marca fallida (modo real)."""
    h = date.fromisoformat(hoy)
    fechas = [(h - timedelta(days=k)).isoformat() for k in range(1, dias + 1)]
    return [f for f in fechas if estado_marca(E, f"marcas/{f}.json") in (None, "fallida")]


def recuperar(E, hoy: str, ahora: datetime, leer=leer_diario, cargar=cargar_con_haiku, maximo: int = RECUPERAR_MAX) -> list:
    """F2-05 (30 de Octubre). En el último intento, lee hasta 'maximo' días atrasados. Antes un día que la nube no leía
    se perdía para siempre. Cada día se lee como último intento, así que termina con marca. Devuelve las fechas intentadas."""
    hechos = []
    for f in pendientes(E, hoy)[:maximo]:
        log(f"Día atrasado {f}. Se intenta leer.")
        try:
            correr(E, f, "real", True, ahora, leer, cargar)
        except Exception:
            traceback.print_exc()
        hechos.append(f)
    return hechos


def main() -> int:
    from servidor import estado as E
    modo = (os.environ.get("MODO") or "real").strip()
    fecha = (os.environ.get("FECHA") or "").strip() or date.today().isoformat()
    ahora = datetime.now()
    final = es_final(ahora, (os.environ.get("INTENTO_FINAL") or "").strip())
    try:
        codigo = correr(E, fecha, modo, final, ahora)
    except Exception:
        traceback.print_exc()
        codigo = 1
    # Los días atrasados solo en el último intento automático, en modo real y sin fecha a mano (F2-05).
    if final and modo == "real" and not (os.environ.get("FECHA") or "").strip():
        recuperar(E, fecha, ahora)
    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
