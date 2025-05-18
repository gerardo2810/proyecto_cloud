# create_vlan_network.py
import subprocess
import sys
import os
import signal

def run(cmd, check=True):
    print(f"➡️ Ejecutando: {cmd}")
    subprocess.run(cmd, shell=True, check=check)

def kill_dnsmasq(vlan_iface):
    print(f"➡️ Buscando procesos dnsmasq en {vlan_iface}...")
    try:
        output = subprocess.check_output(
            f"pgrep -f 'dnsmasq --interface={vlan_iface}'", shell=True, text=True
        )
        for pid in output.strip().split("\n"):
            if pid:
                try:
                    print(f"➡️ Matando dnsmasq con PID {pid}")
                    os.kill(int(pid), signal.SIGKILL)
                except ProcessLookupError:
                    print(f"⚠️ Proceso {pid} ya no existe, ignorando...")
    except subprocess.CalledProcessError:
        print(f"✅ No se encontraron procesos dnsmasq previos en {vlan_iface}")


def delete_namespace(ns_name):
    subprocess.run(f"sudo ip netns del {ns_name}", shell=True, stderr=subprocess.DEVNULL)

def delete_interface(iface, ovs_name):
    subprocess.run(f"sudo ovs-vsctl --if-exists del-port {ovs_name} {iface}", shell=True)
    subprocess.run(f"sudo ip link delete {iface}", shell=True, stderr=subprocess.DEVNULL)

def create_vlan_network(network_name, vlan_id, cidr, dhcp_range):
    ovs_name = "br-int"
    vlan_iface = f"v{vlan_id}t{network_name[:6]}"
    ns_name = f"ns_{network_name}"

    kill_dnsmasq(vlan_iface)
    delete_namespace(ns_name)
    delete_interface(vlan_iface, ovs_name)

    run(f"sudo ovs-vsctl add-port {ovs_name} {vlan_iface} tag={vlan_id} -- set interface {vlan_iface} type=internal")
    run(f"sudo ip link set {vlan_iface} up")

    run(f"sudo ip netns add {ns_name}")
    run(f"sudo ip link set {vlan_iface} netns {ns_name}")
    run(f"sudo ip netns exec {ns_name} ip addr add {cidr} dev {vlan_iface}")
    run(f"sudo ip netns exec {ns_name} ip link set {vlan_iface} up")

    gateway_ip = cidr.split('/')[0]
    run(f"sudo ip netns exec {ns_name} dnsmasq --interface={vlan_iface} --bind-interfaces "
        f"--dhcp-range={dhcp_range},12h --dhcp-option=3,{gateway_ip} --dhcp-option=6,8.8.8.8,8.8.4.4")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Uso: sudo python3 /home/ubuntu/proyecto_cloud/create_vlan_network.py <network_name> <vlan_id> <cidr> <rango_dhcp>")
        sys.exit(1)

    network_name = sys.argv[1]
    vlan_id = int(sys.argv[2])
    cidr = sys.argv[3]
    dhcp_range = sys.argv[4]
    create_vlan_network(network_name, vlan_id, cidr, dhcp_range)
