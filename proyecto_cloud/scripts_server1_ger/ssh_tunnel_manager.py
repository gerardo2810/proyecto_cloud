# ssh_tunnel_manager.py

from sshtunnel import SSHTunnelForwarder
import threading

GATEWAY_IP = "10.20.12.147"
SSH_USER = "ubuntu"
SSH_PASSWORD = "ubuntu"

# Puerto externo de Gateway para cada Worker
SSH_TUNNELS = {
    "10.0.10.2": 5802,
    "10.0.10.3": 5803,
    "10.0.10.4": 5804
}

# Mantén vivos los túneles
active_tunnels = {}

def crear_tunel_vnc(nombre_vm, vnc_port, worker_ip):
    if worker_ip not in SSH_TUNNELS:
        print(f"❌ IP {worker_ip} no registrada en SSH_TUNNELS")
        return
    
    gateway_port = SSH_TUNNELS[worker_ip]
    local_port = 5900 + vnc_port

    if local_port in active_tunnels:
        print(f"🔗 Túnel ya activo para {nombre_vm} en :{vnc_port}")
        return

    def lanzar_tunel():
        try:
            server = SSHTunnelForwarder(
                (GATEWAY_IP, gateway_port),
                ssh_username=SSH_USER,
                ssh_password=SSH_PASSWORD,
                remote_bind_address=('127.0.0.1', local_port),
                local_bind_address=('127.0.0.1', local_port),
            )
            server.start()
            print(f"✅ Túnel VNC para {nombre_vm} activo en :{vnc_port}")
            active_tunnels[local_port] = server
        except Exception as e:
            print(f"❌ Error creando túnel para {nombre_vm} en :{vnc_port} -> {e}")

    threading.Thread(target=lanzar_tunel, daemon=True).start()
