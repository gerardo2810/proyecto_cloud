# Nombre: resource_checker.py
# Retorna los recursos disponibles de los workers remotos

import paramiko
from custom_logger import registrar_log


usuario = 'ubuntu'
password = 'ubuntu'

# Comando para obtener CPU, RAM y disco libres (puedes ajustarlo según tu worker)
CMD = (
    "CPU=$(nproc); "
    "RAM=$(free -m | awk '/Mem:/ {print $7}'); "
    "DISK=$(df / --output=avail -m | tail -1); "
    "echo $CPU $RAM $DISK"
)

def consultar_worker(ip):
    cliente = paramiko.SSHClient()
    cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cliente.connect(ip, username=usuario, password=password)
    stdin, stdout, stderr = cliente.exec_command(CMD)
    salida = stdout.read().decode().strip()
    cliente.close()
    try:
        cpu, ram, disco = map(int, salida.split())
        return {'cpu': cpu, 'ram': ram, 'almacenamiento': disco}
    except:
        return {'cpu': 0, 'ram': 0, 'almacenamiento': 0}

def obtener_recursos_disponibles(workers):
    recursos = {}
    for nombre, ip in workers.items():
        recursos[nombre] = consultar_worker(ip)
    return recursos

# Ejemplo de uso
if __name__ == "__main__":
    workers = {
        "worker1": "10.0.10.2",
        "worker2": "10.0.10.3",
        "worker3": "10.0.10.4"
    }
    print(obtener_recursos_disponibles(workers))