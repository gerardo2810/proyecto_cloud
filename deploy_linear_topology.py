# Nombre: deploy_linear_topology.py
# Despliega una topología lineal de hasta 4 VMs en workers con recursos validados

import sys
import random
import os, json
from resource_checker import obtener_recursos_disponibles
from remote_utils import run_remote, run_local
import subprocess
import time
import threading
import socket

# IPs de los workers
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

IMAGENES_DISPONIBLES = {
    "1": "cirros-0.5.1-x86_64-disk.img",
    "2": "ubuntu-22.04-server-cloudimg-amd64.img"
}

def generar_vlan_id():
    return random.randint(1, 255)

def crear_red_vlan(nombre_topo, vlan_id):
    if vlan_id > 255:
        raise ValueError("El ID de VLAN no puede ser mayor a 255 para mantener el formato 10.0.VLAN.0")
    nombre_red = f"vlan{vlan_id}_{nombre_topo}"
    cidr = f"10.0.{vlan_id}.1/29"
    rango_dhcp = f"10.0.{vlan_id}.2,10.0.{vlan_id}.6"
    run_local(f"sudo python3 create_vlan_network.py {nombre_red} {vlan_id} {cidr} {rango_dhcp}")
    return nombre_red

def generar_nombre_tap(nombre_vm, vlan_id):
    return f"{nombre_vm}_{vlan_id}"

def puerto_vnc_abierto(puerto):
    try:
        with socket.create_connection(("127.0.0.1", 5900 + puerto), timeout=2):
            return True
    except Exception:
        return False

def crear_tunel_ssh(vm_name, vnc_port, worker_ip):
    local_port = 5900 + vnc_port
    ssh_port = SSH_TUNNELS[worker_ip]
    cmd = f"ssh -f -N -L {local_port}:localhost:{local_port} ubuntu@10.20.12.147 -p {ssh_port}"

    def intentar_tunel():
        while True:
            if not puerto_vnc_abierto(vnc_port):
                subprocess.run(cmd, shell=True)
            time.sleep(1000)  

    threading.Thread(target=intentar_tunel, daemon=True).start()

def guardar_topologia(nombre_topo, tipo, vms_info, vlan_ids):
    os.makedirs("topologias", exist_ok=True)
    path = f"topologias/{nombre_topo}.json"
    with open(path, "w") as f:
        json.dump({
            "nombre": nombre_topo,
            "tipo": tipo,
            "vms": vms_info,
            "vlans": vlan_ids
        }, f, indent=2)

def desplegar_topologia_lineal(nombre_topo, vms, imagenes):
    num_vms = len(vms)
    recursos = obtener_recursos_disponibles(WORKERS)
    vms_info = []
    vlan_ids = []
    

    # Asignación de VMs a workers basados en disponibilidad
    for i in range(num_vms):
        cpu, ram, almacenamiento = vms[i]
        for nombre, ip in recursos.items():
            if ip['cpu'] >= cpu and ip['ram'] >= ram and ip['almacenamiento'] >= almacenamiento:
                recursos[nombre]['cpu'] -= cpu
                recursos[nombre]['ram'] -= ram
                recursos[nombre]['almacenamiento'] -= almacenamiento
                vms_info.append({
                    'nombre': f"vm{i+1}_{nombre_topo}",
                    'worker': WORKERS[nombre],
                    'vnc': i + 1,
                    'interfaces': []
                })
                break
        else:
            print("❌ No hay suficientes recursos disponibles en los workers")
            sys.exit(1)

    # Crear VLANs e interfaces para conectar las VMs en cadena
    for i in range(num_vms - 1):
        vlan_id = generar_vlan_id()
        crear_red_vlan(nombre_topo, vlan_id)
        vlan_ids.append(vlan_id)

        tap1 = generar_nombre_tap(i+1, vlan_id)
        tap2 = generar_nombre_tap(i+2, vlan_id)

        vms_info[i]['interfaces'].append((vlan_id, tap1))
        vms_info[i + 1]['interfaces'].append((vlan_id, tap2))

    # Crear las VMs remotamente con sus interfaces
    for idx, vm in enumerate(vms_info):
        cpu, ram, almacenamiento = vms[idx]
        args = [
            vm['nombre'],
            'br-int',
            str(vm['vnc']),
            str(cpu),
            str(ram),
            str(almacenamiento),
            imagenes[idx]
        ]

        for vlan_id, tap_name in vm['interfaces']:
            args.append(f"{vlan_id}:{tap_name}")

        arg_string = ' '.join(args)
        run_remote(vm['worker'], f"python3 create_vm_multi_iface.py {arg_string}")
        crear_tunel_ssh(vm['nombre'], vm['vnc'], vm['worker'])
    

    guardar_topologia(nombre_topo, "lineal", vms_info, vlan_ids)

    print("\n🎯 PUCP DEPLOYER | Puertos VNC asignados:")
    for vm in vms_info:
        print(f"✅ {vm['nombre']} (Worker {vm['worker']}) → VNC :{vm['vnc']}")

if __name__ == "__main__":
    print("❌ Este script no debe ejecutarse directamente con parámetros fijos. Usa main.py para orquestación.")
