"""Texto nuevo de la alerta de vale vista sin dato (aprobado por Diego el 10 de Noviembre de 2026, motor\\vale_vista.py NO_ENCONTRADA).
Las alertas ya cargadas guardan el texto viejo escrito tal cual. Este script lo cambia por el nuevo y nada más. No toca fechas,
remates ni lo agendado, y no llama a Haiku. Deja la base igual que si se hubiera cargado con el código nuevo.
Sin --aplicar solo muestra. Con --aplicar exige un respaldo del mismo día en respaldos.
Uso. python -m db.migrar_texto_sin_dato RUTA_BASE [--aplicar]
"""
import sys, sqlite3, datetime as dt
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor.vale_vista import NO_ENCONTRADA

VIEJO = "La IA no encontró la regla del vale vista. Revísala en el aviso."


def main():
    ruta, aplicar = Path(sys.argv[1]), "--aplicar" in sys.argv
    if aplicar:
        hoy = dt.date.today().isoformat()
        from db.respaldo import carpeta_de
        if not any(carpeta_de(ruta).glob(f"{ruta.stem}_{hoy}*.db")):
            print(f"Falta un respaldo de hoy ({hoy}) en respaldos. No se tocó nada."); sys.exit(1)
    con = sqlite3.connect(ruta)
    n = con.execute("SELECT COUNT(*) FROM alertas WHERE tipo = 'dato_faltante' AND texto = ?", (VIEJO,)).fetchone()[0]
    otros = con.execute("SELECT COUNT(*) FROM alertas WHERE tipo <> 'dato_faltante' AND texto = ?", (VIEJO,)).fetchone()[0]
    print(f"Alertas con el texto viejo {n}. Con otro tipo {otros}.")
    if aplicar and n:
        with con:
            con.execute("UPDATE alertas SET texto = ? WHERE tipo = 'dato_faltante' AND texto = ?", (NO_ENCONTRADA, VIEJO))
        print("Integridad", con.execute("PRAGMA integrity_check").fetchone()[0])
    print("Quedan con el texto viejo", con.execute("SELECT COUNT(*) FROM alertas WHERE texto = ?", (VIEJO,)).fetchone()[0],
          "y con el nuevo", con.execute("SELECT COUNT(*) FROM alertas WHERE texto = ?", (NO_ENCONTRADA,)).fetchone()[0])
    con.close()


if __name__ == "__main__":
    main()
