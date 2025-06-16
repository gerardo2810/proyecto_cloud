#eliminar_topologia.py
import json
import os
from remote_utils import run_remote, run_local
TOPOLOGIAS_PATH = "topologias_guardadas"

def eliminar_topologia(nombre):
    path = os.path.join(TOPOLOGIAS_PATH, f"{nombre}.json")
    if not os.path.exists(path):
        print("❌ Topología no encontrada")
        return
    with open(path) as f:
        topo = json.load(f)

    for vm in topo["vms"]:
        run_remote(vm["worker"], f"sudo pkill -f {vm['nombre']}")
        for _, tap in vm["interfaces"]:
            run_remote(vm["worker"], f"sudo ip link del {tap}")

    for vlan_id in topo["vlans"]:
        red = f"vlan{vlan_id}_{nombre}"
        iface = f"v{vlan_id}tvlan{str(vlan_id)[:2]}"
        ns = f"ns_vlan{vlan_id}_{nombre}"
        run_local(f"sudo ip netns del {ns}")
        run_local(f"sudo ip link del {iface}")

    os.remove(path)
    print(f"🗑️ Topología '{nombre}' eliminada")
