"""Reglas confirmadas por el 24° y el 11° Juzgado Civil de Santiago (decisiones de Diego del 6 de Noviembre de 2026, motor\\reglas_tribunal.py).
Aplica la regla a lo ya cargado sin recargar ediciones, para no cambiar los números internos de los remates que Diego tiene
agendados. Deja cada aviso del 24° Civil igual que si se hubiera cargado con el código nuevo (se comprobó contra una carga
completa desde las capturas). No llama a Haiku. Usa solo las respuestas guardadas en ia_respuestas.
Por cada aviso del 24° Civil que no esté descartado.
  Modalidad sin dato. Pasa a presencial con la alerta de la secretaria. Zoom, en línea o mixta suma la alerta de contradicción.
  Vale vista. Rehace el bloque con lo guardado, le aplica la regla y reemplaza fechas, alertas y citas del bloque anterior.
  Un aviso que la IA todavía no leyó (alerta de vale vista no leído) se deja igual. Lo termina retomar con el código nuevo.
Sin --aplicar solo muestra. Con --aplicar exige un respaldo del mismo día en respaldos.
Uso. python -m db.migrar_24_civil RUTA_BASE [--aplicar]
"""
import sys, sqlite3, datetime as dt
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor import reglas_tribunal as RT
from motor import vale_vista as V
from motor.procesar_edicion import bloque_vale_vista
from db.carga import VV_NO_LEIDO


def bloque_guardado(texto, f, h, fecha_ed):
    g = V.leer_guardada(texto)
    if not g or len(g.get("lecturas") or []) < 2:
        return None
    return bloque_vale_vista(V.resolver(g["lecturas"], texto, f, h, fecha_ed))


def main():
    ruta, aplicar = Path(sys.argv[1]), "--aplicar" in sys.argv
    if aplicar:
        hoy = dt.date.today().isoformat()
        from db.respaldo import carpeta_de             # la carpeta respaldos junto a la base, como el respaldo diario
        if not any(carpeta_de(ruta).glob(f"{ruta.stem}_{hoy}*.db")):
            print(f"Falta un respaldo de hoy ({hoy}) en respaldos. No se tocó nada."); sys.exit(1)
    con = sqlite3.connect(ruta)
    con.execute("PRAGMA foreign_keys = ON")
    # 6 de Noviembre, tarde. También el 11° Civil (regla del secretario). La modalidad sigue siendo solo del 24°.
    avisos = con.execute("SELECT a.id, a.texto, e.fecha, a.tribunal FROM avisos a JOIN ediciones e ON e.id = a.edicion_id "
                         "WHERE a.tribunal IN (?, ?) AND a.filtro_estado <> 'descartado' ORDER BY e.fecha, a.orden", (RT.TRIB_24, RT.TRIB_11)).fetchall()
    n = {"avisos": len(avisos), "modalidad": 0, "vale_vista": 0, "sin_leer": 0, "sin_cambio": 0}
    with con:
        for aid, texto, fecha_ed, trib in avisos:
            mods = {r[0] for r in con.execute("SELECT modalidad FROM remates WHERE aviso_id = ?", (aid,))} if RT.es_24(trib) else set()
            if mods == {"sin_dato"}:
                con.execute("UPDATE remates SET modalidad = 'presencial' WHERE aviso_id = ?", (aid,))
                con.execute("DELETE FROM alertas WHERE aviso_id = ? AND texto = ?", (aid, RT.MOD_SIN_DATO))
                con.execute("INSERT INTO alertas(aviso_id, tipo, texto, origen) VALUES (?,?,?,?)", (aid, "condicion_especial", RT.MOD_SECRETARIA, "codigo"))
                n["modalidad"] += 1
            else:
                for m in mods & set(RT._MOD_TXT):
                    txt = RT.MOD_SECRETARIA_CONTRA.format(RT._MOD_TXT[m])
                    if not con.execute("SELECT 1 FROM alertas WHERE aviso_id = ? AND texto = ?", (aid, txt)).fetchone():
                        con.execute("INSERT INTO alertas(aviso_id, tipo, texto, origen) VALUES (?,?,?,?)", (aid, "contradiccion", txt, "codigo"))
                        n["modalidad"] += 1
            if con.execute("SELECT 1 FROM alertas WHERE aviso_id = ? AND texto = ?", (aid, VV_NO_LEIDO)).fetchone():
                n["sin_leer"] += 1; continue
            f, h, n_rem = con.execute("SELECT fecha_remate, hora_remate, COUNT(*) FROM remates WHERE aviso_id = ?", (aid,)).fetchone()
            viejo = bloque_guardado(texto, f, h, fecha_ed)
            if viejo is None:
                n["sin_leer"] += 1; continue
            nuevo = RT.vale_vista_secretaria(viejo, f, h, trib)
            if nuevo == viejo:
                n["sin_cambio"] += 1; continue
            con.execute("UPDATE remates SET vv_regla = ?, vv_regla_texto = ?, vv_desde = ?, vv_desde_origen = ?, vv_hasta = ?, vv_estado = ? "
                        "WHERE aviso_id = ?", (nuevo["regla"], nuevo["cita"], nuevo["vv_desde"], nuevo["vv_desde_origen"], nuevo["vv_hasta"], nuevo["vv_estado"], aid))
            subs = sorted({r[0] for r in con.execute("SELECT sub_orden FROM alertas WHERE aviso_id = ? AND texto IN (%s)" % ",".join("?" * len(viejo["alertas"])),
                                                       (aid, *[a[1] for a in viejo["alertas"]]))}) if viejo["alertas"] else []
            for tipo, txt, cita in viejo["alertas"]:
                con.execute("DELETE FROM alertas WHERE aviso_id = ? AND tipo = ? AND texto = ?", (aid, tipo, txt))
            for sub in subs:
                for tipo, txt, cita in nuevo["alertas"]:
                    con.execute("INSERT INTO alertas(aviso_id, sub_orden, tipo, texto, cita, origen) VALUES (?,?,?,?,?,?)", (aid, sub, tipo, txt, cita, "codigo"))
            con.execute("DELETE FROM citas WHERE aviso_id = ? AND campo = 'vv_regla_texto'", (aid,))
            if nuevo["cita"]:
                comun = 1 if n_rem == 1 else 0
                for i, c in enumerate([nuevo["cita"]] + nuevo["citas_extra"], start=1):
                    con.execute("INSERT INTO citas(aviso_id, sub_orden, campo, n_cita, valor, cita, metodo, verificada) VALUES (?,?,?,?,?,?,?,?)",
                                (aid, comun, "vv_regla_texto", i, nuevo["regla"], c, "ia", int(c in texto)))
            n["vale_vista"] += 1
        print(n)
        if not aplicar:
            con.rollback(); print("Solo se mostró. Para aplicar agrega --aplicar.")
    print("integridad", con.execute("PRAGMA integrity_check").fetchone()[0])


if __name__ == "__main__":
    main()
