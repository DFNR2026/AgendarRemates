"""Papeleta del vale vista para el banco (11 de Noviembre).

Arma un .docx con la plantilla de Diego (interfaz/plantilla_vale_vista.docx, copia de
Escritos_PJUD/Ejemplo vv banco/EJEMPLO_detalle_deposito_juzgado.docx). Por cada vale van el título
"Vale Vista a nombre de tercero N°i" y las cuatro líneas de la plantilla (A Nombre de, RUT, Monto, Tipo),
con el mismo formato. Entre un vale y otro van dos líneas en blanco. Si el tipo no se sabe, va en blanco.
"""
import io
import re
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

PLANTILLA = Path(__file__).with_name("plantilla_vale_vista.docx")

TIPO_PAPELETA = {"nominativo": "Nominativo (no endosable)", "endosable": "Endosable (no nominativo)"}

_ETIQ = '<w:r><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:b/><w:color w:val="000000"/><w:u w:val="single"/></w:rPr><w:t>{}</w:t></w:r>'
_ESP = '<w:r><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:b/><w:color w:val="000000"/></w:rPr><w:t xml:space="preserve"> </w:t></w:r>'
_VAL = '<w:r><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:color w:val="000000"/></w:rPr><w:t xml:space="preserve">{}</w:t></w:r>'
_LINEA = '<w:p><w:pPr><w:pStyle w:val="Listaconvietas"/><w:spacing w:after="120"/></w:pPr>{}</w:p>'
_SIN_VINETA = ('<w:p><w:pPr><w:pStyle w:val="Listaconvietas"/><w:numPr><w:ilvl w:val="0"/><w:numId w:val="0"/></w:numPr>'
               '<w:spacing w:after="120"/><w:ind w:left="360"/></w:pPr>{}</w:p>')
_TITULO = '<w:r><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:b/><w:color w:val="000000"/></w:rPr><w:t>{}</w:t></w:r>'


def pesos(n):
    return "$" + f"{int(n):,}".replace(",", ".")


def _linea(etiqueta, valor):
    cuerpo = _ETIQ.format(escape(etiqueta)) + _ESP
    if valor:
        cuerpo += _VAL.format(escape(valor))
    return _LINEA.format(cuerpo)


def _bloque(i, v):
    partes = [_SIN_VINETA.format(_TITULO.format(f"Vale Vista a nombre de tercero N°{i}")),
              _linea("A Nombre de:", v.get("a_nombre_de") or ""),
              _linea("RUT:", v.get("rut") or ""),
              _linea("Monto:", pesos(v["monto"]) if v.get("monto") else ""),
              _linea("Tipo:", TIPO_PAPELETA.get(v.get("tipo") or "", ""))]
    return "".join(partes)


def generar(vales, plantilla=PLANTILLA):
    """vales es una lista de dicts con a_nombre_de, rut, monto (entero en pesos) y tipo. Devuelve los bytes del docx."""
    if not vales:
        raise ValueError("Sin vales vista")
    blanco = _SIN_VINETA.format("")
    cuerpo = (blanco * 2).join(_bloque(i, v) for i, v in enumerate(vales, 1)) + blanco
    with zipfile.ZipFile(plantilla) as z:
        archivos = {n: z.read(n) for n in z.namelist()}
        infos = z.infolist()
    doc = archivos["word/document.xml"].decode("utf-8")
    ini = doc.index("<w:body>") + len("<w:body>")
    fin = doc.index("<w:sectPr")
    archivos["word/document.xml"] = (doc[:ini] + cuerpo + doc[fin:]).encode("utf-8")
    sal = io.BytesIO()
    with zipfile.ZipFile(sal, "w", zipfile.ZIP_DEFLATED) as z:
        for info in infos:
            z.writestr(info, archivos[info.filename])
    return sal.getvalue()


def nombre_archivo(vales):
    roles = [re.sub(r"[^\w-]", "", v.get("rol") or "") for v in vales]
    roles = [r for r in roles if r]
    base = "VV_" + "_".join(roles[:3]) if roles else "VV"
    return (base + ("_y_otros" if len(roles) > 3 else "") + ".docx")
