import subprocess
import sys
import os
import re
import socket
import random
import signal

def run(cmd):
    print(f"➡️ Ejecutando: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def obtener_puerto_vnc_disponible(puerto_inicial=1, puerto_max=20):
    for p in range(puerto_inicial, puerto_max):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", 5900 + p))
                return p
            except OSError:
                continue
    raise RuntimeError("❌ No hay puertos VNC disponibles entre 5901 y 5920")

def puerto_vnc_libre(vnc_port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("localhost", 5900 + vnc_port))
        s.close()
        return True
    except OSError:
        return False
    
def eliminar_tap(tap_name, ovs_name):
    subprocess.run(f"sudo ovs-vsctl --if-exists del-port {ovs_name} {tap_name}", shell=True)
    subprocess.run(f"sudo ip link delete {tap_name}", shell=True, stderr=subprocess.DEVNULL)

def generar_mac(idx_vm, idx_iface):
    return "20:20:60:{:02x}:{:02x}:{:02x}".format(
        idx_vm & 0xFF,
        idx_iface & 0xFF,
        random.randint(0, 255)
    )

def extraer_idx_vm(nombre_vm):
    match = re.search(r"vm(\d+)", nombre_vm)
    return int(match.group(1)) if match else random.randint(1, 254)

def liberar_disco_qcow(disco_path):
    # Encuentra y mata procesos que usen ese disco
    cmd_buscar = f"sudo lsof {disco_path} | grep qemu | awk '{{print $2}}'"
    try:
        pids = subprocess.check_output(cmd_buscar, shell=True).decode().split()
        for pid in pids:
            print(f"🔪 Matando proceso QEMU con PID: {pid}")
            os.kill(int(pid), signal.SIGKILL)
    except subprocess.CalledProcessError:
        print("ℹ️ No se encontraron procesos usando el disco")

    if os.path.exists(disco_path):
        print(f"🧹 Eliminando disco antiguo: {disco_path}")
        os.remove(disco_path)

def crear_vm(nombre_vm, ovs_name, vnc_port, cpu, ram, almacenamiento, imagen, interfaces):
    idx_vm = extraer_idx_vm(nombre_vm)

    for vlan_id, tap in interfaces:
        eliminar_tap(tap, ovs_name)
        run(f"sudo ip tuntap add mode tap name {tap}")
        run(f"sudo ip link set {tap} up")
        run(f"sudo ovs-vsctl add-port {ovs_name} {tap} tag={vlan_id}")

    disco_path = f"/tmp/{nombre_vm}.qcow2"
    liberar_disco_qcow(disco_path)

    run(f"qemu-img create -f qcow2 -b /var/lib/libvirt/images/{imagen} {disco_path} {almacenamiento}M")

    netdevs = []
    devices = []
    for idx, (_, tap) in enumerate(interfaces):
        netdev_id = f"net{idx}"
        mac = generar_mac(idx_vm, idx)
        netdevs.append(f"-netdev tap,id={netdev_id},ifname={tap},script=no,downscript=no")
        devices.append(f"-device e1000,netdev={netdev_id},mac={mac}")

    # Buscar un puerto VNC libre
    while not puerto_vnc_libre(vnc_port):
        print(f"⚠️ Puerto VNC :{vnc_port} ocupado. Probando siguiente...")
        vnc_port += 1
        
    # Verifica y corrige el puerto VNC
    puerto_vnc_final = obtener_puerto_vnc_disponible(vnc_port)

        # Verifica y corrige el puerto VNC
    puerto_vnc_final = obtener_puerto_vnc_disponible(vnc_port)

    cmd = f"sudo qemu-system-x86_64 -enable-kvm -m {ram} -smp {cpu} -hda {disco_path} " \
        f"{' '.join(netdevs)} {' '.join(devices)} -vnc :{puerto_vnc_final} -daemonize"
    print(f"🖥️  Lanzando VM {nombre_vm} en puerto VNC :{puerto_vnc_final}")
    
    try:
        run(cmd)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al lanzar la VM {nombre_vm}: {e}")
        sys.exit(1)




if __name__ == "__main__":
    if len(sys.argv) < 8:
        print("Uso: python3 create_vm_multi_iface.py <vm_name> <ovs> <vnc> <cpu> <ram> <almacenamiento> <imagen> <vlan:tap> ...")
        sys.exit(1)

    nombre_vm = sys.argv[1]
    ovs_name = sys.argv[2]
    vnc_port = int(sys.argv[3])
    cpu = int(sys.argv[4])
    ram = int(sys.argv[5])
    almacenamiento = int(sys.argv[6])
    imagen = sys.argv[7]

    interfaces = []
    for par in sys.argv[8:]:
        vlan, tap = par.split(":")
        interfaces.append((int(vlan), tap))

    crear_vm(nombre_vm, ovs_name, vnc_port, cpu, ram, almacenamiento, imagen, interfaces)
