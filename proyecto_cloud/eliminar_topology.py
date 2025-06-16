import subprocess
import re
import os
from log_launcher import get_logger

logger = get_logger()
TOPONOMBRE = input("🔧 Nombre de la topología a eliminar: ").strip()
WORKERS = ["10.0.10.2", "10.0.10.3", "10.0.10.4"]

def run_local(cmd):
    print(f"➡️ {cmd}")
    subprocess.run(cmd, shell=True)

def run_remote(ip, cmd):
    print(f"➡️ [Remoto {ip}] {cmd}")
    subprocess.run(f"ssh ubuntu@{ip} '{cmd}'", shell=True)

### 🧹 HEADNODE
def limpiar_headnode():
    logger.info(f"🧹 Limpiando HEADNODE de '{TOPONOMBRE}'")
    ns_list = subprocess.getoutput("ip netns list").splitlines()
    ns_topo = [ns.split()[0] for ns in ns_list if TOPONOMBRE in ns]

    for ns in ns_topo:
        vlan_id = re.search(r"vlan(\d+)_", ns)
        if not vlan_id:
            continue
        vlan = vlan_id.group(1)

        iface_vlan = f"v{vlan}tvlan{vlan}"
        veth_br = f"veth{vlan}-br"

        run_local(f"sudo ip netns delete {ns} || true")
        run_local(f"sudo ip link del {veth_br} || true")
        run_local(f"sudo ovs-vsctl --if-exists del-port br-int {iface_vlan}")
        run_local(f"sudo rm -rf /etc/netns/{ns}")
        run_local(f"sudo iptables -t nat -D POSTROUTING -s 10.0.{vlan}.0/29 -o ens3 -j MASQUERADE || true")
        run_local(f"sudo iptables -D FORWARD -i {veth_br} -o ens3 -j ACCEPT || true")
        run_local(f"sudo iptables -D FORWARD -i ens3 -o {veth_br} -m state --state RELATED,ESTABLISHED -j ACCEPT || true")

### 🧹 WORKERS
def limpiar_workers():
    for ip in WORKERS:
        logger.info(f"🧹 Limpiando WORKER {ip} de '{TOPONOMBRE}'")
        print(f"\n🧹 Limpiando WORKER {ip}...")

        run_remote(ip, f"ps aux | grep 'qemu-system' | grep 'vm[1-4]_{TOPONOMBRE}\.qcow2' | awk '{{print $2}}' | xargs -r sudo kill -9")
        run_remote(ip, f"sudo find /tmp -name 'vm*_{TOPONOMBRE}.qcow2' -delete")

        interfaces = subprocess.getoutput(f"ssh ubuntu@{ip} 'ip link show'").splitlines()
        tap_list = [line.split(":")[1].strip() for line in interfaces if f"_{TOPONOMBRE}" in line]
        for tap in tap_list:
            run_remote(ip, f"sudo ovs-vsctl --if-exists del-port br-int {tap}")
            run_remote(ip, f"sudo ip link del {tap} || true")

### ▶️ EJECUCIÓN
logger.info(f"🧹 Eliminando topología '{TOPONOMBRE}'")
print(f"\n🚨 Eliminando topología '{TOPONOMBRE}' en todos los nodos...")
limpiar_headnode()
limpiar_workers()
logger.info(f"✅ Limpieza completa de la topología '{TOPONOMBRE}'")
print("\n✅ Limpieza completa de la topología.")