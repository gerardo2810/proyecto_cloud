# Nombre: remote_utils.py
# Utilidades para ejecutar comandos locales y remotos

import subprocess
import paramiko
from custom_logger import registrar_log


usuario = 'ubuntu'
password = 'ubuntu'

def run_local(cmd):
    print(f"➡️ Ejecutando localmente: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def run_remote(ip, cmd, capture_output=False):
    print(f"➡️ Ejecutando remotamente en {ip}: {cmd}")
    cliente = paramiko.SSHClient()
    cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cliente.connect(ip, username=usuario, password=password)
    comando = f"cd ~/proyecto_cloud && echo '{password}' | sudo -S {cmd}"
    stdin, stdout, stderr = cliente.exec_command(comando, get_pty=True)

    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    cliente.close()

    if capture_output:
        # ⚠️ Filtrar errores y capturar solo el último número (vnc_port)
        for line in out.splitlines()[::-1]:
            if line.strip().isdigit():
                return line.strip()
        raise ValueError(f"❌ No se pudo extraer un VNC válido.\nSTDOUT:\n{out}\nSTDERR:\n{err}")
    else:
        print(out)
        print(err)
