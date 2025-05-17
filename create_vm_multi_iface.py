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

def obtener_puerto_vnc_remoto(inicio=1, fin=100):
    for i in range(inicio, fin):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", 5900 + i))
                return i
        except:
            continue
    raise RuntimeError("❌ No hay puertos VNC disponibles en el Worker")

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

def crear_seed_iso(nombre_vm):
    user_data = f"""#cloud-config
users:
  - name: ubuntu
    sudo: ALL=(ALL) NOPASSWD:ALL
    groups: users, admin
    home: /home/ubuntu
    shell: /bin/bash
    lock_passwd: false
    ssh_pwauth: true
    passwd: $6$rounds=4096$salt$uQhXUZiGOKkPqIqDTV89EemkoGPcLQ/Whg6cbJcEojkRT1KUgrNe9P4J3tGObh4Fq6aosxl0gIl7RtE2zIlVf.

chpasswd:
  list: |
    ubuntu:ubuntu
  expire: False

runcmd:
  - sed -i 's|http://.*.ubuntu.com/ubuntu|http://10.0.10.1|g' /etc/apt/sources.list
  - apt update || true
  - apt install -y tcpdump || true
  - wget -O /tmp/arping.deb http://10.0.10.1/iputils-arping_20190709-3_amd64.deb || true
  - dpkg -i /tmp/arping.deb || true
  - apt install -f -y || true
"""

    meta_data = f"""instance-id: {nombre_vm}
local-hostname: {nombre_vm}
"""

    seed_dir = f"/tmp/seed_{nombre_vm}"
    os.makedirs(seed_dir, exist_ok=True)
    with open(f"{seed_dir}/user-data", "w") as f:
        f.write(user_data)
    with open(f"{seed_dir}/meta-data", "w") as f:
        f.write(meta_data)

    seed_img = f"/tmp/seed_{nombre_vm}.iso"
    run(f"genisoimage -output {seed_img} -volid cidata -joliet -rock {seed_dir}/user-data {seed_dir}/meta-data")
    return seed_img




def crear_vm(nombre_vm, ovs_name, cpu, ram, almacenamiento, imagen, interfaces):
    idx_vm = extraer_idx_vm(nombre_vm)

    for vlan_id, tap in interfaces:
        eliminar_tap(tap, ovs_name)
        run(f"sudo ip tuntap add mode tap name {tap}")
        run(f"sudo ip link set {tap} up")
        run(f"sudo ovs-vsctl add-port {ovs_name} {tap} tag={vlan_id}")

    disco_path = f"/tmp/{nombre_vm}.qcow2"
    liberar_disco_qcow(disco_path)

    base_img_path = f"/var/lib/libvirt/images/{imagen}"
    is_ubuntu = "ubuntu" in imagen.lower() or "focal" in imagen.lower()

    # ✅ Lógica dinámica según tipo de imagen
    if is_ubuntu:
        run(f"qemu-img convert -O qcow2 {base_img_path} {disco_path}")
    else:
        run(f"qemu-img create -f qcow2 -b {base_img_path} {disco_path} {almacenamiento}M")

    netdevs = []
    devices = []
    for idx, (_, tap) in enumerate(interfaces):
        netdev_id = f"net{idx}"
        mac = generar_mac(idx_vm, idx)
        netdevs.append(f"-netdev tap,id={netdev_id},ifname={tap},script=no,downscript=no")
        devices.append(f"-device e1000,netdev={netdev_id},mac={mac}")

    vnc_port = obtener_puerto_vnc_remoto()

    seed_arg = ""
    if is_ubuntu:
        seed_img = crear_seed_iso(nombre_vm)
        seed_arg = f"-drive file={seed_img},format=raw,if=virtio,readonly=on"

    cmd = f"sudo qemu-system-x86_64 -enable-kvm -m {ram} -smp {cpu} -hda {disco_path} " \
          f"{' '.join(netdevs)} {' '.join(devices)} {seed_arg} -vnc :{vnc_port} -daemonize"

    print(f"🖥️  Lanzando VM {nombre_vm} en puerto VNC :{vnc_port}")

    try:
        run(cmd)
        print(vnc_port)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al lanzar la VM {nombre_vm}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 8:
        sys.exit(1)

    nombre_vm = sys.argv[1]
    ovs_name = sys.argv[2]
    cpu = int(sys.argv[4])
    ram = int(sys.argv[5])
    almacenamiento = int(sys.argv[6])
    imagen = sys.argv[7]

    interfaces = []
    for par in sys.argv[8:]:
        vlan, tap = par.split(":")
        interfaces.append((int(vlan), tap))

    crear_vm(nombre_vm, ovs_name, cpu, ram, almacenamiento, imagen, interfaces)
