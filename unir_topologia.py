# unir_topologias.py
# Une dos topologías existentes conectando una VM de cada una mediante una nueva VLAN

import json
import os
import random
import subprocess
import sys
from remote_utils import run_remote, run_local

def generar_vlan_id():
    return random.randint(1, 255)

def crear_red_vlan(nombre_union, vlan_id):
    nombre_red = f"vlan{vlan_id}_{nombre_union}"
    cidr = f"10.0.{vlan_id}.1/29"
    rango_dhcp = f"10.0.{vlan_id}.2,10.0.{vlan_id}.6"
    run_local(f"sudo python3 create_vlan_network.py {nombre_red} {vlan_id} {cidr} {rango_dhcp}")
    return nombre_red

def unir_topologias(id1, id2, vm1, vm2):
    path1 = f"topologias/topo{id1}.json"
    path2 = f"topologias/topo{id2}.json"
    
    if not os.path.exists(path1) or not os.path.exists(path2):
        print("❌ Una o ambas topologías no existen")
        sys.exit(1)

    with open(path1) as f1, open(path2) as f2:
        topo1 = json.load(f1)
        topo2 = json.load(f2)

    # Obtener VM origen y destino
    vm_origen = next(vm for vm in topo1['vms'] if vm['nombre'] == vm1)
    vm_destino = next(vm for vm in topo2['vms'] if vm['nombre'] == vm2)

    vlan_id = generar_vlan_id()
    crear_red_vlan(f"union_{id1}_{id2}", vlan_id)

    # Nombres de TAP
    tap1 = f"{vm1}_vlan{vlan_id}"
    tap2 = f"{vm2}_vlan{vlan_id}"

    # Agregar interfaz a la VM origen
    cmd1 = f"sudo ip tuntap add mode tap name {tap1}"
    cmd2 = f"sudo ip link set {tap1} up"
    cmd3 = f"sudo ovs-vsctl add-port br-int {tap1} tag={vlan_id}"
    run_remote(vm_origen['worker'], f"{cmd1} && {cmd2} && {cmd3}")

    # Agregar interfaz a la VM destino
    cmd4 = f"sudo ip tuntap add mode tap name {tap2}"
    cmd5 = f"sudo ip link set {tap2} up"
    cmd6 = f"sudo ovs-vsctl add-port br-int {tap2} tag={vlan_id}"
    run_remote(vm_destino['worker'], f"{cmd4} && {cmd5} && {cmd6}")

    # Registrar en los archivos
    vm_origen['interfaces'].append({"vlan": vlan_id, "tap": tap1})
    vm_destino['interfaces'].append({"vlan": vlan_id, "tap": tap2})
    topo1['vlan_ids'].append(vlan_id)
    topo2['vlan_ids'].append(vlan_id)

    with open(path1, 'w') as f1, open(path2, 'w') as f2:
        json.dump(topo1, f1, indent=2)
        json.dump(topo2, f2, indent=2)

    print(f"✅ Topologías {id1} y {id2} unidas correctamente mediante VLAN {vlan_id}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Uso: python3 unir_topologias.py <id_topo1> <id_topo2> <vm1> <vm2>")
        sys.exit(1)

    unir_topologias(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
