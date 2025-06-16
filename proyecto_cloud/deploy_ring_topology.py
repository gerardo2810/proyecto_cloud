import sys
import os, json
import random
from resource_checker import obtener_recursos_disponibles
from remote_utils import run_remote, run_local
import subprocess
import time
import threading
import socket
from itertools import cycle
from custom_logger import registrar_log
from configurar_internet import configurar_salida_internet_vlan

WORKERS = {
    "worker1": "10.0.10.2",
    "worker2": "10.0.10.3",
    "worker3": "10.0.10.4"
}

SSH_TUNNELS = {
    "10.0.10.2": 5802,
    "10.0.10.3": 5803,
    "10.0.10.4": 5804
}

MAX_VMS = 4

def generar_vlan_id():
    return random.randint(1, 255)

def crear_red_vlan(nombre_topo, vlan_id):
    if vlan_id > 255:
        raise ValueError("El ID de VLAN no puede ser mayor a 255 para mantener el formato 10.0.VLAN.0")
    nombre_red = f"vlan{vlan_id}_{nombre_topo}"
    cidr = f"10.0.{vlan_id}.1/29"
    rango_dhcp = f"10.0.{vlan_id}.2,10.0.{vlan_id}.6"
    run_local(f"sudo python3 /home/ubuntu/proyecto_cloud/create_vlan_network.py {nombre_red} {vlan_id} {cidr} {rango_dhcp}")
    configurar_salida_internet_vlan(vlan_id, nombre_topo)
    return nombre_red

def generar_nombre_tap(nombre_vm, vlan_id, idx_iface):
    # ejemplo: vm1_v43_0 → 11 caracteres
    nombre_corto = nombre_vm.split("_")[0]  # extrae vm1
    return f"{nombre_corto}_v{vlan_id}_{idx_iface}"


def guardar_topologia(nombre_topo, tipo, vms_info, vlan_ids, usuario, rol):
    os.makedirs("topologias", exist_ok=True)
    path = f"/home/ubuntu/proyecto_cloud/topologias/{nombre_topo}.json"

    # Asegurarse de que todas las VMs tienen campos completos
    for vm in vms_info:
        if "cpu" not in vm:
            vm["cpu"] = 1
        if "ram" not in vm:
            vm["ram"] = 400
        if "disco" not in vm:
            vm["disco"] = 400
        if "imagen" not in vm:
            vm["imagen"] = "cirros-0.5.1-x86_64-disk.img"
        if "carpeta" not in vm:
            vm["carpeta"] = "/tmp"
        if "interfaces" not in vm:
            vm["interfaces"] = []  # Asegurarse que siempre exista

    # Estructura de la topología
    topologia = {
        "nombre": nombre_topo,
        "tipo": tipo,
        "vms": vms_info,
        "vlans": vlan_ids,
        "usuario_creador": usuario,
        "rol_creador": rol
    }

    with open(path, "w") as f:
        json.dump(topologia, f, indent=2)


def desplegar_topologia_anillo(nombre_topo, vms, imagenes, usuario, rol):
    num_vms = len(vms)
    recursos = obtener_recursos_disponibles(WORKERS)
    vms_info = []
    vlan_ids = []
    

    round_robin = cycle(WORKERS.keys())
    for i in range(num_vms):
        cpu, ram, almacenamiento = vms[i]
        intentos = 0
        asignado = False
        while intentos < len(WORKERS):
            worker = next(round_robin)
            recurso = recursos[worker]
            if recurso['cpu'] >= cpu and recurso['ram'] >= ram and recurso['almacenamiento'] >= almacenamiento:
                recurso['cpu'] -= cpu
                recurso['ram'] -= ram
                recurso['almacenamiento'] -= almacenamiento
                vms_info.append({
                    'nombre': f"vm{i+1}_{nombre_topo}",
                    'worker': WORKERS[worker],
                    'vnc': None,
                    'interfaces': [],
                    'cpu': cpu,
                    'ram': ram,
                    'disco': almacenamiento,
                    'imagen': imagenes[i],
                    'carpeta': "/tmp"
                })
                asignado = True
                break
            intentos += 1
        if not asignado:
            print("❌ No hay suficientes recursos disponibles en los workers para una VM.")
            sys.exit(1)


    

    for i in range(num_vms):
        vm_actual = vms_info[i]
        vm_siguiente = vms_info[(i + 1) % num_vms]

        vlan_id = generar_vlan_id()
        crear_red_vlan(nombre_topo, vlan_id)
        vlan_ids.append(vlan_id)
        tap_actual = generar_nombre_tap(vm_actual['nombre'], vlan_id, 0)
        tap_siguiente = generar_nombre_tap(vm_siguiente['nombre'], vlan_id, 1)


        if (vlan_id, tap_actual) not in vm_actual['interfaces']:
            vm_actual['interfaces'].append((vlan_id, tap_actual))

        if (vlan_id, tap_siguiente) not in vm_siguiente['interfaces']:
            vm_siguiente['interfaces'].append((vlan_id, tap_siguiente))




    for idx, vm in enumerate(vms_info):
        cpu = vm['cpu']
        ram = vm['ram']
        almacenamiento = vm['disco']
        imagen = vm['imagen']

        args = [
            vm['nombre'],
            'br-int',
            str(vm['vnc']),
            str(cpu),
            str(ram),
            str(almacenamiento),
            imagenes[idx][0] if isinstance(imagenes[idx], list) else imagenes[idx]
        ]
        for vlan_id, tap_name in vm['interfaces']:
            args.append(f"{vlan_id}:{tap_name}")

        arg_string = ' '.join(args)
        output = run_remote(vm['worker'], f"python3 /home/ubuntu/proyecto_cloud/create_vm_multi_iface.py {arg_string}", capture_output=True)
        vm['vnc'] = int(output.strip())
        

    guardar_topologia(nombre_topo, "anillo", vms_info, vlan_ids, usuario, rol)

    print("\n🎯 PUCP DEPLOYER | Puertos VNC asignados - Topología Anillo:")
    for vm in vms_info:
        print(f"✅ {vm['nombre']} (Worker {vm['worker']}) → VNC :{vm['vnc']}")
