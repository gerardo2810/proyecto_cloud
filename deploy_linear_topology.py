# deploy_linear_topology.py
import sys
import random
import os
import json
import subprocess
import time
import threading
import socket
from resource_checker import obtener_recursos_disponibles
from remote_utils import run_remote, run_local
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

def generar_vlan_id():
    return random.randint(1, 255)

def crear_red_vlan(nombre_topo, vlan_id):
    if vlan_id > 255:
        raise ValueError("El ID de VLAN no puede ser mayor a 255")
    nombre_red = f"vlan{vlan_id}_{nombre_topo}"
    cidr = f"10.0.{vlan_id}.1/29"
    rango_dhcp = f"10.0.{vlan_id}.2,10.0.{vlan_id}.6"
    run_local(f"sudo python3 create_vlan_network.py {nombre_red} {vlan_id} {cidr} {rango_dhcp}")
    configurar_salida_internet_vlan(vlan_id, nombre_topo)
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
    cmd = f"ssh -f -N -L {local_port}:localhost:{local_port} ubuntu@10.20.12.51 -p {ssh_port}"

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

def desplegar_topologia_lineal_from_json(payload: dict):
    nombre_topo = payload["nombre"]
    vms = payload["vms"]  # Lista de diccionarios con keys: cpu, ram, disco
    imagenes = payload["imagenes"]  # Lista con nombre de imagen por VM

    num_vms = len(vms)
    recursos = obtener_recursos_disponibles(WORKERS)
    vms_info = []
    vlan_ids = []

    # Asignar recursos
    for i in range(num_vms):
        cpu, ram, almacenamiento = vms[i]["cpu"], vms[i]["ram"], vms[i]["disco"]
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
            raise RuntimeError("❌ No hay recursos disponibles en los workers")

    # Crear red y asignar interfaces
    for i in range(num_vms - 1):
        vlan_id = generar_vlan_id()
        crear_red_vlan(nombre_topo, vlan_id)
        vlan_ids.append(vlan_id)

        tap1 = generar_nombre_tap(i+1, vlan_id)
        tap2 = generar_nombre_tap(i+2, vlan_id)

        vms_info[i]['interfaces'].append((vlan_id, tap1))
        vms_info[i + 1]['interfaces'].append((vlan_id, tap2))

    # Crear VMs
    for idx, vm in enumerate(vms_info):
        cpu = vms[idx]["cpu"]
        ram = vms[idx]["ram"]
        disco = vms[idx]["disco"]
        args = [
            vm['nombre'],
            'br-int',
            str(vm['vnc']),
            str(cpu),
            str(ram),
            str(disco),
            imagenes[idx]
        ]
        for vlan_id, tap in vm['interfaces']:
            args.append(f"{vlan_id}:{tap}")
        run_remote(vm['worker'], f"python3 create_vm_multi_iface.py {' '.join(args)}")
        crear_tunel_ssh(vm['nombre'], vm['vnc'], vm['worker'])

    guardar_topologia(nombre_topo, "lineal", vms_info, vlan_ids)

    return {
        "mensaje": f"✅ Topología lineal '{nombre_topo}' desplegada con éxito.",
        "vnc": [
            {"vm": vm["nombre"], "worker": vm["worker"], "vnc": vm["vnc"]}
            for vm in vms_info
        ]
    }
