import os
import json
from datetime import datetime


# Carpeta donde se guardarán los logs
LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Mapeo de severidades tipo syslog RFC 5424
SEVERITY_LEVELS = {
    "emergency": 0,
    "alert": 1,
    "critical": 2,
    "error": 3,
    "warning": 4,
    "notice": 5,
    "info": 6,
    "debug": 7
}

def registrar_log(topologia, usuario, facility, severity, mnemonic, descripcion):
    """
    Registra un evento en formato syslog personalizado.

    :param topologia: Nombre de la topología (ej: 'topologia1')
    :param usuario: Nombre del usuario que ejecuta (ej: 'Gerardo')
    :param facility: Tipo del evento (ej: 'vm', 'tap', 'namespace', etc.)
    :param severity: Nivel de severidad (ej: 'info', 'error', 'critical', etc.)
    :param mnemonic: Código corto del evento (ej: 'VMCREATE', 'TAPDEL')
    :param descripcion: Texto explicativo del evento
    """

    now = datetime.now()
    timestamp = now.strftime("%b %d %H:%M:%S")  # Ej: May 18 21:30:45
    severity_code = SEVERITY_LEVELS.get(severity.lower(), 6)  # default: info

    # Encabezado tipo Cisco
    header = f"{topologia}-{usuario} {timestamp}: %{facility.upper()}-{severity_code}-{mnemonic.upper()}"
    log_line = f"{header}: {descripcion}"

    # Mostrar en consola
    print(log_line)

    # Construir log estructurado
    log_entry = {
        "topologia_usuario": f"{topologia}-{usuario}",
        "timestamp": timestamp,
        "facility": facility.upper(),
        "severity": severity,
        "severity_code": severity_code,
        "mnemonic": mnemonic.upper(),
        "description": descripcion
    }

    # Guardar en archivo JSON por topología-usuario
    log_file = os.path.join(LOG_DIR, f"{topologia}-{usuario}.json")

    # Leer contenido anterior (si existe)
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            logs = json.load(f)
    else:
        logs = []

    logs.append(log_entry)

    with open(log_file, "w") as f:
        json.dump(logs, f, indent=2)
