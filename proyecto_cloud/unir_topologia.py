import json
import random
import os
import hashlib
import shutil
import sys
from remote_utils import run_remote
from configurar_internet import configurar_salida_internet_vlan
from create_vlan_network import create_vlan_network
from custom_logger import registrar_log


def generar_vlan_id(existentes):
    while True:
        vlan = random.randint(10, 250)
        if vlan not in existentes:
            return vlan

def generar_nombre_tap(vm_nombre, vlan_id):
    # Genera un nombre TAP único por VM y VLAN (máximo 15 caracteres)
    hash_id = hashlib.md5(f"{vm_nombre}_{vlan_id}".encode()).hexdigest()[:4]
    vm_id = ''.join(filter(str.isdigit, vm_nombre.split('_')[0]))[:2] or '0'
    return f"t{vlan_id}{vm_id}_{hash_id}"[:15]

def agregar_interfaz_remota(vm, vlan_id, tap_name):
    ovs_name = "br-int"
    cmd = f"sudo ip tuntap add mode tap name {tap_name} && " \
          f"sudo ip link set {tap_name} up && " \
          f"sudo ovs-vsctl add-port {ovs_name} {tap_name} tag={vlan_id}"
    run_remote(vm['worker'], cmd)

def relanzar_vm(vm):
    imagen = vm.get('imagen')
    if not imagen:
        print(f"❌ ERROR: La VM '{vm['nombre']}' no tiene una imagen definida en el JSON.")
        return
    args = [
        vm['nombre'],
        'br-int',
        str(vm.get('vnc', 1)),
        str(vm.get('cpu', 1)),
        str(vm.get('ram', 400)),
        str(vm.get('disco', 400)),
        imagen
    ]

    for iface in vm['interfaces']:
        if isinstance(iface, dict):
            vlan_id = iface['vlan']
            tap = iface['tap']
        else:
            vlan_id, tap = iface
        args.append(f"{vlan_id}:{tap}")

    cmd = f"python3 /home/ubuntu/proyecto_cloud/create_vm_multi_iface.py {' '.join(args)}"
    run_remote(vm['worker'], cmd)

def unir_topologias(json_topo1, json_topo2, vm1_name, vm2_name, nombre_nueva):
    path1 = f"/home/ubuntu/proyecto_cloud/topologias/{json_topo1}.json"
    path2 = f"/home/ubuntu/proyecto_cloud/topologias/{json_topo2}.json"
    with open(path1) as f1, open(path2) as f2:
        topo1 = json.load(f1)
        topo2 = json.load(f2)

    todas_vlans = set(topo1['vlans'] + topo2['vlans'])
    nueva_vlan = generar_vlan_id(todas_vlans)

    vm1 = next((vm for vm in topo1['vms'] if vm['nombre'] == vm1_name), None)
    vm2 = next((vm for vm in topo2['vms'] if vm['nombre'] == vm2_name), None)

    if vm1 is None:
        print(f"❌ VM '{vm1_name}' no encontrada en topología '{json_topo1}'")
        sys.exit(1)
    if vm2 is None:
        print(f"❌ VM '{vm2_name}' no encontrada en topología '{json_topo2}'")
        sys.exit(1)

    tap1 = generar_nombre_tap(vm1_name, nueva_vlan)
    tap2 = generar_nombre_tap(vm2_name, nueva_vlan)

    vm1['interfaces'].append({"vlan": nueva_vlan, "tap": tap1})
    vm2['interfaces'].append({"vlan": nueva_vlan, "tap": tap2})

    agregar_interfaz_remota(vm1, nueva_vlan, tap1)
    agregar_interfaz_remota(vm2, nueva_vlan, tap2)

    nombre_red = f"vlan{nueva_vlan}_{nombre_nueva}"
    cidr = f"10.0.{nueva_vlan}.1/29"
    dhcp_range = f"10.0.{nueva_vlan}.2,10.0.{nueva_vlan}.6"
    os.system(f"sudo python3 /home/ubuntu/proyecto_cloud/create_vlan_network.py {nombre_red} {nueva_vlan} {cidr} {dhcp_range}")
    configurar_salida_internet_vlan(nueva_vlan, nombre_nueva)

    nueva_topo = {
        "nombre": nombre_nueva,
        "tipo": "unida",
        "vms": topo1['vms'] + topo2['vms'],
        "vlans": list(todas_vlans | {nueva_vlan})
    }

    os.makedirs("/home/ubuntu/proyecto_cloud/topologias", exist_ok=True)
    with open(f"/home/ubuntu/proyecto_cloud/topologias/{nombre_nueva}.json", "w") as f:
        json.dump(nueva_topo, f, indent=2)

    print(f"\n🔁 Relanzando VMs {vm1_name} y {vm2_name} con nueva interfaz...")
    relanzar_vm(vm1)
    relanzar_vm(vm2)

    print(f"\n✅ Topologías '{json_topo1}' y '{json_topo2}' unidas en '{nombre_nueva}' con VLAN {nueva_vlan}\n")

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Uso: python3 /home/ubuntu/proyecto_cloud/unir_topologias.py topo1 topo2 vm1 vm2 nombre_nueva")
        sys.exit(1)

    unir_topologias(
        sys.argv[1],  # topo1
        sys.argv[2],  # topo2
        sys.argv[3],  # vm1
        sys.argv[4],  # vm2
        sys.argv[5]   # nombre_nueva
    )
