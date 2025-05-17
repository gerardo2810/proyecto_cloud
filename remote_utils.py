# Nombre: remote_utils.py
# Utilidades para ejecutar comandos locales y remotos

import subprocess
import paramiko

SSH_TUNNELS = {
    "10.0.10.2": 5802,
    "10.0.10.3": 5803,
    "10.0.10.4": 5804
}

usuario = 'ubuntu'
password = 'ubuntu'

def run_local(cmd):
    print(f"➡️ Ejecutando localmente: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def run_remote(ip_worker, cmd):
    print(f"➡️ Ejecutando remotamente en worker {ip_worker} (vía gateway 10.20.12.51) → {cmd}")
    ssh_port = SSH_TUNNELS.get(ip_worker)
    if not ssh_port:
        raise ValueError(f"No se encontró puerto SSH para worker {ip_worker}")

    gateway_ip = "10.20.12.51"

    cliente = paramiko.SSHClient()
    cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cliente.connect(gateway_ip, port=ssh_port, username=usuario, password=password)

    # Ya no asumimos que existe ~/proyecto_cloud
    comando = f"echo '{password}' | sudo -S {cmd}"

    stdin, stdout, stderr = cliente.exec_command(comando, get_pty=True)
    print(stdout.read().decode())
    print(stderr.read().decode())
    cliente.close()