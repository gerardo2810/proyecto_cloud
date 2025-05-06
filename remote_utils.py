# Nombre: remote_utils.py
# Utilidades para ejecutar comandos locales y remotos

import subprocess
import paramiko

usuario = 'ubuntu'
password = 'ubuntu'

def run_local(cmd):
    print(f"➡️ Ejecutando localmente: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def run_remote(ip, cmd):
    print(f"➡️ Ejecutando remotamente en {ip}: {cmd}")
    cliente = paramiko.SSHClient()
    cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cliente.connect(ip, username=usuario, password=password)
    comando = f"cd ~/proyecto_cloud && echo '{password}' | sudo -S {cmd}"
    stdin, stdout, stderr = cliente.exec_command(comando, get_pty=True)
    print(stdout.read().decode())
    print(stderr.read().decode())
    cliente.close()
