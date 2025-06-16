import os
import re
import sys
import getpass
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
from resource_checker_dinamico import ejecutar_reporte_recursos



HISTORIAL = []

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


def menu_principal(usuario, rol,token):
    
    if token:
        print("Bienvenido", usuario,rol)


        print("1️⃣  Crear Topología")
        print("2️⃣  Historial de topologías")
        
        if rol == "SuperAdministrador":
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

def gestionar_flavors(usuario, rol):
    while True:
        print("\n📦 Gestión de Flavors:")
        print("1. Listar flavors")
        print("2. Crear nuevo flavor")
        print("3. Eliminar flavor")
        print("4. Editar flavor")
        print("0. Volver")
        op = input("Seleccione una opción: ")

        if op == "1":
            listar_flavors(usuario, rol)
        elif op == "2":
            while True:
                nombre = input("Nombre del flavor: ").strip()
                if nombre:
                    break
                print("❌ El nombre no puede estar vacío.")
            cpu = input_num("CPU: ")
            ram = input_num("RAM (MB): ")
            disco = input_num("Disco (MB): ")
            print("1. Cirros\n2. Ubuntu")
            img_sel = input("Imagen base (1/2): ")
            imagen = IMAGENES.get(img_sel, "cirros-0.5.1-x86_64-disk.img")
            crear_flavor(nombre, cpu, ram, disco, imagen, usuario, rol)
        elif op == "3":
            nombre = input("🔴 Nombre del flavor a eliminar: ").strip()
            eliminar_flavor(nombre, usuario, rol)
        elif op == "4":
            flavors = cargar_flavors()
            flavors_validos = {
                nombre: datos for nombre, datos in flavors.items()
                if rol == "SuperAdministrador" or datos.get("usuario_creador") == usuario
            }

            if not flavors_validos:
                print("⚠️ No tienes flavors disponibles para editar.")
                continue

            print("\n✏️ Flavors que puedes editar:")
            for nombre in flavors_validos:
                print(f" - {nombre}")

            while True:
                nombre_flavor = input("🔧 Nombre del flavor a editar (Enter para cancelar): ").strip()
                if not nombre_flavor:
                    print("❌ Operación cancelada.")
                    break
                if nombre_flavor in flavors_validos:
                    break
                print("❌ Nombre inválido o sin permiso. Intenta nuevamente.")

            if nombre_flavor:
                cpu = input_num("Nuevo CPU: ") or None
                ram = input_num("Nuevo RAM (MB): ") or None
                disco = input_num("Nuevo Disco (MB): ") or None
                print("1. Cirros\n2. Ubuntu\nEnter para mantener imagen actual")
                img_sel = input("Nueva imagen base (1/2): ").strip()
                imagen = IMAGENES.get(img_sel) if img_sel in IMAGENES else None
                editar_flavor(nombre_flavor, cpu=cpu, ram=ram, disco=disco, imagen=imagen, usuario=usuario, rol=rol)
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



def crear_topologia(usuario,rol):
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
                vms.append((cpu, ram, disco, IMAGENES[img_sel]))

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
    imagenes = [img[0] if isinstance(img, list) else img for (_, _, _, img) in vms]
    vms_info = [(cpu, ram, disco) for (cpu, ram, disco, _) in vms]

    if diseno == "1":
        vms_info = [(cpu, ram, disco) for (cpu, ram, disco, _) in vms]
        desplegar_topologia_lineal(nombre, vms_info, imagenes, usuario, rol)
        tipo = "Lineal"
    elif diseno == "2":
        vms_info = [(cpu, ram, disco) for (cpu, ram, disco, _) in vms]
        desplegar_topologia_anillo(nombre, vms_info, imagenes, usuario, rol)
        tipo = "Anillo"
    else:
        print("❌ Diseño no válido")
        return

    


    HISTORIAL.append({"nombre": nombre, "vms": num_vms, "imagen": "Cirros", "diseño": tipo})
    print("\n✅ Topología desplegada exitosamente 🚀\n")

def mostrar_historial_simple():
    print("\n🗂️  ==== Historial de Topologías ====")
    print(f"{'#':<4} {'Nombre':<12} {'Diseño':<10} {'VMs':<4} {'Imagen':<20}")
    print("-" * 50)
    for i, topo in enumerate(HISTORIAL):
        print(f"{i+1:<4} {topo['nombre']:<12} {topo['diseño']:<10} {topo['vms']:<4} {topo['imagen']:<20}")

def ver_historial(usuario, rol):
    carpeta = "/home/ubuntu/proyecto_cloud/topologias"
    archivos = [f for f in os.listdir(carpeta) if f.endswith(".json")]

    topologias = []
    for archivo in archivos:
        ruta = os.path.join(carpeta, archivo)
        with open(ruta, "r") as f:
            data = json.load(f)
            creador = data.get("usuario_creador")
            rol_creador = data.get("rol_creador", "")

            if rol == "SuperAdministrador" or (rol == "Administrador" and creador == usuario):
                topologias.append(data)

    if not topologias:
        print("📭 No hay topologías registradas para tu usuario/rol.")
        return

    print("\n🗂️  Historial de Topologías Disponibles:")
    print("-" * 100)
    print(f"{'N°':<4} {'Nombre':<15} {'Tipo':<10} {'# VMs':<7} {'Imagen base':<35} {'Creador':<15}")
    print("-" * 100)

    for i, topo in enumerate(topologias, start=1):
        vms = topo.get("vms", [])
        vms_count = len(vms)
        imagen = vms[0].get("imagen", "N/A") if vms_count > 0 else "N/A"
        print(f"{i:<4} {topo['nombre']:<15} {topo['tipo']:<10} {vms_count:<7} {imagen:<35} {topo.get('usuario_creador', 'N/A'):<15}")

    print("-" * 100)

    while True:
        op = input("\nIngrese el número de la topología para acciones (borrar/unir) o Enter para volver: ").strip()
        if not op:
            return
        if op.isdigit() and 1 <= int(op) <= len(topologias):
            index = int(op) - 1
            break
        print("❌ Número inválido. Intente nuevamente.")

    nombre_topo = topologias[index]['nombre']
    vms_topo = len(topologias[index].get('vms', []))

    print(f"\n🔧 Acciones para topología '{nombre_topo}':")
    print("1. Borrar topología")
    print("2. Unir con otra topología")

    while True:
        accion = input("Seleccione acción (1/2): ").strip()
        if accion in ["1", "2"]:
            break
        print("❌ Opción no válida. Ingrese 1 o 2.")

    if accion == "1":
        eliminar_topologia(nombre_topo)
        os.remove(os.path.join(carpeta, f"{nombre_topo}.json"))
        print(f"✅ Topología '{nombre_topo}' borrada.")
        return

    elif accion == "2":
        while True:
            otro = input("Ingrese número de la otra topología a unir: ").strip()
            if otro.isdigit():
                otro_index = int(otro) - 1
                if 0 <= otro_index < len(topologias) and otro_index != index:
                    break
            print("❌ Índice no válido o topología duplicada. Intente nuevamente.")

        topo2 = topologias[otro_index]['nombre']
        vms_topo2 = len(topologias[otro_index].get('vms', []))

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
                if not any(t['nombre'] == nombre_nueva for t in topologias):
                    break
                else:
                    print("❌ Ya existe una topología con ese nombre.")
            else:
                print("❌ El nombre no debe exceder 10 caracteres.")

        unir_topologias(nombre_topo, topo2, vm1, vm2, nombre_nueva)
        print(f"✅ Topologías '{nombre_topo}' y '{topo2}' unidas como '{nombre_nueva}'.")

def ver_recursos():
    print("\n📊 Consultando recursos...")
    ejecutar_reporte_recursos()

def ver_logs():
    print("\n📄 Mostrando logs de /var/log/pucp_deployer.log\n")
    os.system("tail -n 40 /var/log/pucp_deployer.log")

if __name__ == "__main__":
    token = os.environ.get("TOKEN")
    usuario = os.environ.get("USER")
    rol = os.environ.get("ROL")

    if token:
        print(f"Bienvenido {usuario} con rol {rol} 👋")
        
        while True:
            opcion = menu_principal(usuario, rol, token)
            # resto de tu ciclo principal
            if opcion == "1":
                crear_topologia(usuario,rol)
            elif opcion == "2":
                ver_historial(usuario,rol)
            elif opcion == "3":
                if rol == "SuperAdministrador":
                    ver_recursos()
                else:
                    print("❌ Opción no válida para su rol")
            elif opcion == "4":
                if rol == "SuperAdministrador":
                    ver_logs()
                else:
                    print("❌ Opción no válida para su rol")
            elif opcion == "5":
                gestionar_flavors(usuario, rol)
            elif opcion == "0":
                print("👋 Saliendo...")
                break
            else:
                print("❌ Opción no válida")
            input("\n🔁 Presione Enter para continuar...")
            clear()
