import subprocess
import sys

def run_cmd(cmd, check=True):
    print(f"➡️ Ejecutando: {cmd}")
    subprocess.run(cmd, shell=True, check=check)

def configurar_salida_internet_vlan(vlan_id, nombre_topologia):
    vlan_id = int(vlan_id)
    ns = f"ns_vlan{vlan_id}_{nombre_topologia}"
    veth_br = f"veth{vlan_id}-br"
    veth_ns = f"veth{vlan_id}-ns"
    ip_host = f"169.254.{vlan_id}.1/30"
    ip_ns = f"169.254.{vlan_id}.2/30"
    red_vlan = f"10.0.{vlan_id}.0/29"

    print(f"\n🔧 Configurando salida a Internet para VLAN {vlan_id}, topología {nombre_topologia}")

    # 0. Eliminar interfaces anteriores si existen
    run_cmd(f"sudo ip link del {veth_br} || true")

    # 1. Crear par veth
    run_cmd(f"sudo ip link add {veth_br} type veth peer name {veth_ns}")

    # 2. Conectar un extremo al host
    run_cmd(f"sudo ip addr add {ip_host} dev {veth_br}")
    run_cmd(f"sudo ip link set {veth_br} up")

    # 3. Conectar el otro extremo al namespace
    run_cmd(f"sudo ip link set {veth_ns} netns {ns}")
    run_cmd(f"sudo ip netns exec {ns} ip addr add {ip_ns} dev {veth_ns}")
    run_cmd(f"sudo ip netns exec {ns} ip link set {veth_ns} up")

    # 4. Establecer default route en el namespace hacia el host
    run_cmd(f"sudo ip netns exec {ns} ip route replace default via {ip_host.split('/')[0]}")

    # 5. Habilitar IP forwarding en el host
    run_cmd("sudo sysctl -w net.ipv4.ip_forward=1")

    # 6. NAT en el HOST para tráfico del namespace y de las VMs
    run_cmd(f"sudo iptables -t nat -A POSTROUTING -s {red_vlan} -o ens3 -j MASQUERADE")
    run_cmd(f"sudo iptables -t nat -A POSTROUTING -s {ip_ns.split('/')[0]} -o ens3 -j MASQUERADE")

    # 7. Reenvío entre veth y ens3 en el host
    run_cmd(f"sudo iptables -A FORWARD -i {veth_br} -o ens3 -j ACCEPT")
    run_cmd(f"sudo iptables -A FORWARD -i ens3 -o {veth_br} -m state --state RELATED,ESTABLISHED -j ACCEPT")

    # 8. NAT dentro del namespace para que VMs salgan usando su gateway 10.0.X.1
    run_cmd(f"sudo ip netns exec {ns} iptables -t nat -A POSTROUTING -s {red_vlan} -o {veth_ns} -j MASQUERADE")

    # 9. IP forwarding dentro del namespace
    run_cmd(f"sudo ip netns exec {ns} sysctl -w net.ipv4.ip_forward=1")

    print(f"\n✅ Namespace {ns} y VMs en 10.0.{vlan_id}.0/29 tienen salida a Internet.\n")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python3 configurar_salida_internet.py <vlan_id> <nombre_topologia>")
        sys.exit(1)

    vlan_id = sys.argv[1]
    nombre_topologia = sys.argv[2]
    configurar_salida_internet_vlan(vlan_id, nombre_topologia)
