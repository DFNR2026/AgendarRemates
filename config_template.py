# PLANTILLA. Copiar como config.py (que NO va a GitHub) y completar las credenciales.
from pathlib import Path

RAIZ = Path(__file__).resolve().parent

# El Mercurio Digital
MERCURIO_USER = ""   # RUT sin puntos ni guion
MERCURIO_PASS = ""   # contraseña
MERCURIO_BASE_URL = "https://digital.elmercurio.com"

# Carpetas (relativas al proyecto)
PERFIL_NAVEGADOR = RAIZ / "perfil_navegador"   # sesión guardada, separada de la del Mercurio
CAPTURAS = RAIZ / "capturas"                    # texto de cada página leída, por fecha

# Supabase, proyecto Agendar_Calendario (20 de Octubre). La agenda baja de aquí lo que la nube leyó cada mañana.
SUPABASE_URL = "https://hkxxufbzerkbdpjaowrz.supabase.co"
SUPABASE_KEY = ""          # clave secreta (secret o service_role) del proyecto. Nunca va a GitHub.
CARGA_REAL_APROBADA = False   # la agenda real (agendar_remates.db) solo se actualiza cuando Diego lo apruebe
