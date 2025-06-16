import os
import sys
import getpass
import threading
import requests
import paramiko
from deploy_linear_topology import desplegar_topologia_lineal
from deploy_ring_topology import desplegar_topologia_anillo
from unir_topologia import unir_topologias
from eliminar_topologia import eliminar_topologia
from custom_logger import registrar_log


HISTORIAL = []
AUTH_SERVICE_URL = "http://127.0.0.1:8000/login"

IMAGENES = {
    "1": "cirros-0.5.1-x86_64-disk.img",
    "2": "focal-server-cloudimg-amd64.img"
}

SSH_TUNNELS = {
    "10.0.10.2": 5802,
    "10.0.10.3": 5803,
    "10.0.10.4": 5804
}

WORKERS = {
    "worker1": "10.0.10.2",
    "worker2": "10.0.10.3",
    "worker3": "10.0.10.4"
}

def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

def login():
    clear()
    print("""
    ██████╗ ██╗   ██╗ ██████╗██████╗ ██████╗ ███████╗██████╗ ██╗      ██████╗  ██╗   ██╗███████╗██████╗
    ██╔══██╗██║   ██║██╔════╝██╔══██╗██╔══██╗██╔════╝██╔══██╗██║     ██╔═══██╗ ╚██╗ ██╔╝██╔════╝██╔══██╗  
    ██████╔╝██║   ██║██║     ██████╔╝██║  ██║█████╗  ██████╔╝██║     ██║   ██║  ╚████╔╝ █████╗  ██████╔╝
    ██╔═══╝ ██║   ██║██║     ██╔═══╝ ██║  ██║██╔══╝  ██╔═══╝ ██║     ██║   ██║   ╚██╔╝  ██╔══╝  ██╔══██╗ 
    ██║     ╚██████╔╝╚██████╗██║     ██████╔╝███████╗██║     ███████╗╚██████╔╝    ██║   ███████╗██║  ██║ 
    ╚═╝      ╚═════╝  ╚═════╝╚═╝     ╚═════╝ ╚══════╝╚═╝     ╚══════╝ ╚═════╝     ╚═╝   ╚══════╝╚═╝  ╚═╝ """)

    print("==== Bienvenido a PUCPDEPLOYER ====")

    intentos = 3
    while intentos > 0:
        usuario = input("👤 Usuario: ")
        clave = getpass.getpass("🔐 Contraseña: ")

        # Realizar el POST al microservicio de autenticación con JSON
        response = requests.post(
            AUTH_SERVICE_URL, 
            json={"username": usuario, "contrasenia": clave}
        )

        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            usuario = data.get("username")
            rol = data.get("rol")

            if token and usuario and rol:
                print(f"\n✅ Acceso concedido. Token recibido.")
                return usuario, rol, token
            else:
                print("\n⚠️ La respuesta no contiene los campos esperados.")
                return None
        else:
            intentos -= 1
            print(f"\n❌ Credenciales incorrectas. Quedan {intentos} intento(s).\n")

    print("\n❌ Se agotaron los intentos. Programa terminado.\n")
    sys.exit(1)

def leer_entrada(chan):
    while True:
        try:
            # Leer una línea completa del usuario
            linea = sys.stdin.readline()
            if not linea:
                break
            chan.send(linea)
        except Exception:
            break

def ejecutar_remoto_ssh(usuario, rol, token):
    ssh_host = "10.20.12.147"
    ssh_port = 5801
    ssh_user = "ubuntu"
    ssh_password = "ubuntu"

    comando = f'/home/ubuntu/proyecto_cloud/run_main_remoto.sh "{token}" "{usuario}" "{rol}"'

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ssh_host, port=ssh_port, username=ssh_user, password=ssh_password)

        chan = client.invoke_shell()
        chan.send(comando)

        # Iniciar hilo para leer la entrada del usuario y enviar al canal SSH
        hilo_entrada = threading.Thread(target=leer_entrada, args=(chan,), daemon=True)
        hilo_entrada.start()

        while True:
            if chan.recv_ready():
                salida = chan.recv(1024).decode('utf-8')
                if not salida:
                    break
                print(salida, end='')

            if chan.closed:
                break

        client.close()

    except Exception as e:
        print(f"Error conectando o ejecutando comando remoto: {e}")

if __name__ == "__main__":
    usuario, rol, token = login()
    if token and usuario and rol:
        ejecutar_remoto_ssh(usuario, rol, token)