"""Mutaciones de motor\\requisitos.py y de la caja de la ficha (13 de Noviembre de 2026). Se corre desde la carpeta del proyecto con
python -m pruebas.mutaciones_requisitos. Cambia una línea, corre pruebas.test_requisitos, espera una FALLA y restaura el archivo.
Borra las copias compiladas antes y después de cada una. Una prueba que se cae no cuenta como detectada."""
import subprocess,shutil,sys,os
R='motor/requisitos.py'; D='interfaz/datos.py'; H='interfaz/agenda.html'
M=[(R,'if ay and ay.start() < pos:','if ay:'),
 (R,'elif _ENVIAR.search(o) and not despues:','elif _ENVIAR.search(o):'),
 (R,'and not no_postor and not _OJV_NO.search(oc):','and not no_postor:'),
 (R,'UMBRAL = 0.80','UMBRAL = 0.70'),
 (R,'MIN_CAUSAS = 10 ','MIN_CAUSAS = 5 '),
 (R,'_CLAVE_NO = re.compile(r"exceptuad", re.I)','_CLAVE_NO = re.compile(r"zzzzzzzzz", re.I)'),
 (R,'if todos and a - todos[-1][1] <= 2:','if todos and a - todos[-1][1] <= -1:'),
 (R,'c = _PLAZO_FIN.search(txt, 12)','c = None'),
 (R,'distintos = bool(del_link and del_id and del_link != del_id)','distintos = False'),
 (R,'        if _NO_AVISO.search(o):','        if False:'),
 (R,'and modalidad == "presencial"):','and False):'),
 (R,'_ABREV = re.compile(r"\\b(hrs|hs|','_ABREV = re.compile(r"\\b(hs|'),
 (R,'_?)\\s?@\\s?pjud\\.\\s?cl\\b", re.I)','_?)@pjud\\.\\s?cl\\b", re.I)'),
 (D,'"requisitos": requisitos_manual(m), "pubs"','"requisitos": RQ.para_ficha(m["tribunal"], None, m["modalidad"]), "pubs"'),
 (H,'  ${requisitosHTML(it)}\n',''),
 (R,'r"podr[áa]\\s+ser\\s+retirado|transferencias\\s+realizadas|escritura", re.I)\n_NO_POSTOR','r"podr[áa]\\s+ser\\s+retirado|devoluci|transferencias\\s+realizadas|escritura", re.I)\n_NO_POSTOR'),
 (R,'(?:correo|e-?mail)[^.]{0,140}?(?:tel[ée]f[oó]n|celular)','(?:correo|e-?mail)[^.]{0,140}?(?:tel[ée]fon|celular)'),
 (R,'        adv.append(A_MANO if texto is None else ROTO)','        adv.append(ROTO)'),
 (R,'    del_id = re.sub(r"\\s", "", i.group(1)) if i else None','    del_id = i.group(1) if i else None'),
 (R,'frases.setdefault(o, _frase(o, pos))','_frase(o, pos)'),
 (R,'(?:,?\\s+(?:entre|de|desde)\\s+(?:las\\s+)?','(?:,?\\s+(?:zzentre|de|desde)\\s+(?:las\\s+)?'),
 (R,'al_vv = AL_ENTREGAR if junto else None','al_vv = None'),
 (R,'cuando = mas.get("cuando") if not mas.get("plazo") else None','cuando = mas.get("cuando")'),
 (H,'${r.cuando?`<div>','${false?`<div>'),
 (D,'q = RQ.para_ficha(m["tribunal"], a["texto"] if a else None, m["modalidad"])','q = RQ.para_ficha(m["tribunal"], None, m["modalidad"])'),
 (D,'return d.get(f"{(tribunal or \'\').strip()}|{rol}-{anio}")','return d.get(f"{rol}-{anio}")'),
 (H,"'Frase '+(fr.indexOf(r.frase)+1)","'Frase '+fr.indexOf(r.frase)"),
 (H,'rs.filter(r=>r.frase===f).map(r=>','rs.map(r=>'),
 (R,"|(?<![\\s.][A-ZÁÉÍÓÚÑ])\\.(?:-)?\\s+(?=[a-záéíóúñ]{2,}\\b)\")","\")"),
 (R,"|(?<![\\s.][A-ZÁÉÍÓÚÑ])\\.(?:-)?","|\\.(?:-)?"),
 (R,'plazo=_plazo(o, pos) or plazo_previo)','plazo=_plazo(o, pos))'),
 (R,'and not _DESPUES.search(previa) and not correos(previa) else None)','and not correos(previa) else None)'),
 (R,'if k in vistos or (not mas.get("plazo") and any(v[:3] == k[:3] for v in vistos)):','if k in vistos:'),
]
def limpia():
    for d in ('motor/__pycache__','interfaz/__pycache__','pruebas/__pycache__'): shutil.rmtree(d,ignore_errors=True)
def corre():
    r1=subprocess.run([sys.executable,'-m','pruebas.test_requisitos'],capture_output=True,text=True)
    return r1
det=0
for n,(f,a,b) in enumerate(M,1):
    s=open(f,encoding='utf-8').read()
    if s.count(a)!=1: print(n,'NO APLICA',s.count(a),a[:50]); continue
    open(f,'w',encoding='utf-8').write(s.replace(a,b)); limpia()
    try:
        r=corre(); out=r.stdout
        fallas=[l for l in out.splitlines() if l.startswith('FALLA')]
        if 'RESULTADO.' not in out: est='SE CAE (no cuenta)'
        elif fallas: est='detectada'; det+=1
        else: est='SOBREVIVE'
        print(n,est,'|',a[:45],'|',(fallas[0][6:70] if fallas else ''))
    finally:
        open(f,'w',encoding='utf-8').write(s); limpia()
print('detectadas',det,'de',len(M))
