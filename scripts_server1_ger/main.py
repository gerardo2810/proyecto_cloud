import os
import sys
import getpass
import requests
import time
import json
import socket
import subprocess
from deploy_linear_topology import desplegar_topologia_lineal
from deploy_ring_topology import desplegar_topologia_anillo
from unir_topologia import unir_topologias
from eliminar_topologia import eliminar_topologia
from flavor_manager import crear_flavor, listar_flavors, obtener_flavor, cargar_flavors, eliminar_flavor, editar_flavor
from custom_logger import registrar_log

HISTORIAL = []
AUTH_SERVICE_URL = "http://127.0.0.1:8000/login"

IMAGENES = {
    "1": "cirros-0.5.1-x86_64-disk.img",
    "2": "focal-server-cloudimg-amd64.img"
}

SSH_TUNNELS = {
    "10.0.10.2": 5802,
    "10.0.10.3": 5803,
    "10.0.10.4": 5804
}

WORKERS = {
    "worker1": "10.0.10.2",
    "worker2": "10.0.10.3",
    "worker3": "10.0.10.4"
}

def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

def login():
    clear()
    print("""
    ██████╗ ██╗   ██╗ ██████╗██████╗ ██████╗ ███████╗██████╗ ██╗      ██████╗  ██╗   ██╗███████╗██████╗
    ██╔══██╗██║   ██║██╔════╝██╔══██╗██╔══██╗██╔════╝██╔══██╗██║     ██╔═══██╗ ╚██╗ ██╔╝██╔════╝██╔══██╗  
    ██████╔╝██║   ██║██║     ██████╔╝██║  ██║█████╗  ██████╔╝██║     ██║   ██║  ╚████╔╝ █████╗  ██████╔╝
    ██╔═══╝ ██║   ██║██║     ██╔═══╝ ██║  ██║██╔══╝  ██╔═══╝ ██║     ██║   ██║   ╚██╔╝  ██╔══╝  ██╔══██╗ 
    ██║     ╚██████╔╝╚██████╗██║     ██████╔╝███████╗██║     ███████╗╚██████╔╝    ██║   ███████╗██║  ██║ 
    ╚═╝      ╚═════╝  ╚═════╝╚═╝     ╚═════╝ ╚══════╝╚═╝     ╚══════╝ ╚═════╝     ╚═╝   ╚══════╝╚═╝  ╚═╝ """)
                                                                          
    print("==== Bienvenido a PUCPDEPLOYER ====")

    intentos = 3
    while intentos > 0:
        usuario = input("👤 Usuario: ")
        clave = getpass.getpass("🔐 Contraseña: ")

        # Realizar el POST al microservicio de autenticación con JSON
        response = requests.post(
            AUTH_SERVICE_URL, 
            json={"username": usuario, "contrasenia": clave}
        )

        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            usuario = data.get("username")
            rol = data.get("rol")

            if token and usuario and rol:
                print(f"\n✅ Acceso concedido. Token recibido.")
                return usuario, rol, token
            else:
                print("\n⚠️ La respuesta no contiene los campos esperados.")
                return None
        else:
            intentos -= 1
            print(f"\n❌ Credenciales incorrectas. Quedan {intentos} intento(s).\n")

    print("\n❌ Se agotaron los intentos. Programa terminado.\n")
    sys.exit(1)

def menu_principal():
    print("1️⃣  Crear Topología")
    print("2️⃣  Historial de topologías")
    print("3️⃣  Recursos de servidores")
    print("4️⃣  Logs")
    print("5️⃣  Gestionar Flavors")
    print("0️⃣  Salir")
    return input("\nSeleccione una opción: ")

def input_num(msg):
    while True:
        val = input(msg)
        if val.isdigit():
            return int(val)
        print("❗ Ingrese solo números.")

def generar_tabla_flavors(flavors_dict):
    tabla = "\n📦 Flavors disponibles:\n"
    tabla += "-" * 75 + "\n"
    tabla += f"{'Nombre':<20} {'CPU':<5} {'RAM (MB)':<10} {'Disco (MB)':<12} Imagen\n"
    tabla += "-" * 75 + "\n"
    for nombre, datos in flavors_dict.items():
        tabla += f"{nombre:<20} {datos['cpu']:<5} {datos['ram']:<10} {datos['disco']:<12} {datos['imagen']}\n"
    tabla += "-" * 75 + "\n"
    return tabla  

def gestionar_flavors():
    while True:
        print("\n📦 Gestión de Flavors:")
        print("1. Listar flavors")
        print("2. Crear nuevo flavor")
        print("3. Eliminar flavor")
        print("4. Editar flavor")
        print("0. Volver")
        op = input("Seleccione una opción: ")

        if op == "1":
            listar_flavors()
        elif op == "2":
            nombre = input("Nombre del flavor: ").strip()
            cpu = input_num("CPU: ")
            ram = input_num("RAM (MB): ")
            disco = input_num("Disco (MB): ")
            print("1. Cirros\n2. Ubuntu")
            img_sel = input("Imagen base (1/2): ")
            imagen = IMAGENES.get(img_sel, "cirros-0.5.1-x86_64-disk.img")
            crear_flavor(nombre, cpu, ram, disco, imagen)
        elif op == "3":
            nombre = input("🔴 Nombre del flavor a eliminar: ").strip()
            eliminar_flavor(nombre)
        elif op == "4":
            nombre = input("✏️ Nombre del flavor a editar: ").strip()
            cpu = input_num("Nuevo CPU: ") or None
            ram = input_num("Nuevo RAM (MB): ") or None
            disco = input_num("Nuevo Disco (MB): ") or None
            print("1. Cirros\n2. Ubuntu\nEnter para mantener imagen actual")
            img_sel = input("Nueva imagen base (1/2): ").strip()
            imagen = IMAGENES.get(img_sel) if img_sel in IMAGENES else None
            editar_flavor(nombre, cpu, ram, disco, imagen)
        elif op == "0":
            break
        else:
            print("❌ Opción inválida.")

def validar_cirros_cpu(cpu):
    if cpu != 1:
        print("❌ Para Cirros, CPU debe ser exactamente 1")
        return False
    return True

def validar_cirros_rango(valor, campo):
    if not (300 <= valor <= 700):
        print(f"❌ Para Cirros, {campo} debe estar entre 300 y 700 MB")
        return False
    return True



def crear_topologia():
    while True:
        nombre = input("\n📛 Nombre de la topología (solo letras y números): ").strip()
        if not nombre.isalnum():
            print("❌ Nombre no válido. Solo letras y números sin espacios.")
            continue
        break

    print("\n1. Crear VMs con Flavors\n2. Crear VMs una por una")
    modo = input("Seleccione un modo: ")

    num_vms = input_num("🔢 Cantidad de VMs (2-4): ")
    if num_vms < 2 or num_vms > 4:
        print("❌ Solo se permiten entre 2 y 4 VMs")
        return

    vms = []
    if modo == "1":
        flavors_dict = cargar_flavors()
        if not flavors_dict:
            print("❌ No hay flavors definidos.")
            return
        print(generar_tabla_flavors(flavors_dict))
        for i in range(num_vms):
            print(f"\n🖥️  Selección de flavor para VM{i+1}")
            while True:
                nombre_flavor = input("👉 Ingrese nombre del flavor a usar: ").strip()
                flavor = obtener_flavor(nombre_flavor)
                if flavor:
                    break
                print("❌ Flavor no válido. Intente nuevamente.")
            vms.append((flavor['cpu'], flavor['ram'], flavor['disco'], flavor['imagen']))
    else:
        for i in range(num_vms):
            print(f"\n🖥️  Configuración de VM{i+1}")
            print("📂 Imagen disponible:")
            print("1. Cirros")
            print("2. Ubuntu")
            while True:
                img_sel = input("Seleccione imagen base (1/2): ")
                if img_sel in IMAGENES:
                    break
                print("❌ Imagen no válida. Seleccione 1 o 2.")

            if img_sel == "1":  # Cirros
                while True:
                    cpu = input_num("⚙️  CPU: ")
                    if validar_cirros_cpu(cpu):
                        break
                while True:
                    ram = input_num("📦 RAM (MB): ")
                    if validar_cirros_rango(ram, "RAM"):
                        break
                while True:
                    disco = input_num("💾 Almacenamiento (MB): ")
                    if validar_cirros_rango(disco, "Almacenamiento"):
                        break
            else: # Ubuntu
                cpu = input_num("⚙️  CPU: ")
                ram = input_num("📦 RAM (MB): ")
                disco = input_num("💾 Almacenamiento (MB): ")
                vms.append((cpu, ram, disco, IMAGENES[img_sel]))

    print("\n🔗 Seleccione diseño de topología:")
    print("1. Lineal")
    print("2. Anillo")
    diseno = input("Diseño: ")

    print("\n⚙️  Desplegando topología...\n")
    if diseno == "1":
        imagenes = [img for (_, _, _, img) in vms]
        vms_info = [(cpu, ram, disco) for (cpu, ram, disco, _) in vms]
        desplegar_topologia_lineal(nombre, vms_info, imagenes)
        tipo = "Lineal"
    elif diseno == "2":
        imagenes = [img for (_, _, _, img) in vms]
        vms_info = [(cpu, ram, disco) for (cpu, ram, disco, _) in vms]
        desplegar_topologia_anillo(nombre, vms_info, imagenes)
        tipo = "Anillo"
    else:
        print("❌ Diseño no válido")
        return

    


    HISTORIAL.append({"nombre": nombre, "vms": num_vms, "imagen": "Cirros", "diseño": tipo})
    print("\n✅ Topología desplegada exitosamente 🚀\n")


def ver_historial():
    if not HISTORIAL:
        print("📭 No hay topologías registradas.")
        return
    
    mostrar_historial_simple()

    while True:
        op = input("\nIngrese el número de la topología para acciones (borrar/unir) o Enter para volver: ").strip()
        if not op:
            return
        if op.isdigit() and 1 <= int(op) <= len(HISTORIAL):
            index = int(op) - 1
            break
        print("❌ Número inválido. Intente nuevamente.")

    nombre_topo = HISTORIAL[index]['nombre']
    vms_topo = HISTORIAL[index]['vms']

    print(f"\n🔧 Acciones para topología '{nombre_topo}':")
    print("1. Borrar topología")
    print("2. Unir con otra topología")

    while True:
        accion = input("Seleccione acción (1/2): ").strip()
        if accion in ["1", "2"]:
            break
        print("❌ Opción no válida. Ingrese 1 o 2.")

    if accion == "1":
        HISTORIAL.pop(index)
        eliminar_topologia(nombre_topo)
        print(f"✅ Topología '{nombre_topo}' borrada.")
        return

    elif accion == "2":
        while True:
            otro = input("Ingrese número de la otra topología a unir: ").strip()
            if otro.isdigit():
                otro_index = int(otro) - 1
                if 0 <= otro_index < len(HISTORIAL) and otro_index != index:
                    break
            print("❌ Índice no válido o topología duplicada. Intente nuevamente.")

        topo2 = HISTORIAL[otro_index]['nombre']
        vms_topo2 = HISTORIAL[otro_index]['vms']

        while True:
            vm1 = input(f"Nombre de la VM en '{nombre_topo}' para unir (ej: vm1_{nombre_topo}): ").strip()
            if re.match(r'^vm\d+_' + re.escape(nombre_topo) + r'$', vm1):
                num_vm1 = int(vm1[2:].split('_')[0])
                if 1 <= num_vm1 <= vms_topo:
                    break
            print(f"❌ VM inválida. Debe estar en formato 'vmX_{nombre_topo}' y X debe ser una VM válida.")

        while True:
            vm2 = input(f"Nombre de la VM en '{topo2}' para unir (ej: vm1_{topo2}): ").strip()
            if re.match(r'^vm\d+_' + re.escape(topo2) + r'$', vm2):
                num_vm2 = int(vm2[2:].split('_')[0])
                if 1 <= num_vm2 <= vms_topo2:
                    break
            print(f"❌ VM inválida. Debe estar en formato 'vmX_{topo2}' y X debe ser una VM válida.")

        while True:
            nombre_nueva = input("Ingrese el nombre de la nueva topología unida (máx 10 caracteres): ").strip()
            if len(nombre_nueva) <= 10:
                if not any(t['nombre'] == nombre_nueva for t in HISTORIAL):
                    break
                else:
                    print("❌ Ya existe una topología con ese nombre.")
            else:
                print("❌ El nombre no debe exceder 10 caracteres.")

        unir_topologias(nombre_topo, topo2, vm1, vm2, nombre_nueva)
        print(f"✅ Topologías '{nombre_topo}' y '{topo2}' unidas como '{nombre_nueva}'.")
    
def mostrar_historial_simple():
    print("\n🗂️  ==== Historial de Topologías ====")
    print(f"{'#':<4} {'Nombre':<12} {'Diseño':<10} {'VMs':<4} {'Imagen':<20}")
    print("-" * 50)
    for i, topo in enumerate(HISTORIAL):
        print(f"{i+1:<4} {topo['nombre']:<12} {topo['diseño']:<10} {topo['vms']:<4} {topo['imagen']:<20}")

def ver_recursos():
    print("\n📊 Recursos disponibles:")
    os.system("python3 resource_checker.py")

def ver_logs():
    print("\n📝 ==== Últimos logs de ejecución ====")
    os.system("tail -n 30 /var/log/syslog")

if __name__ == "__main__":
    usuario, rol, token = login()
    while True:
        opcion = menu_principal()
        if opcion == "1":
            crear_topologia()
        elif opcion == "2":
            ver_historial()
        elif opcion == "3":
            ver_recursos()
        elif opcion == "4":
            ver_logs()
        elif opcion == "5":
            gestionar_flavors()
        elif opcion == "0":
            print("👋 Saliendo...")
            break
        else:
            print("❌ Opción no válida")
        input("\n🔁 Presione Enter para continuar...")
        clear()
