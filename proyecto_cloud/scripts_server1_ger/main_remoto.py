import os
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


def menu_principal(usuario, rol, token):
    if token:
        print("Bienvenido", usuario, rol)
        print("1️⃣  Crear Topología")
        print("2️⃣  Historial de topologías")

        if rol == "SuperAdministrador":
            print("3️⃣  Recursos de servidores")
            print("4️⃣  Logs")

        print("0️⃣  Salir")
        return input("\nSeleccione una opción: ")

def input_num(msg):
    while True:
        val = input(msg)
        if val.isdigit():
            return int(val)
        print("❗ Ingrese solo números.")

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
        desplegar_topologia_lineal(nombre, vms_info, imagenes,usuario,rol)
        tipo = "Lineal"
    elif diseno == "2":
        imagenes = [img for (_, _, _, img) in vms]
        vms_info = [(cpu, ram, disco) for (cpu, ram, disco, _) in vms]
        desplegar_topologia_anillo(nombre, vms_info, imagenes,usuario,rol)
        tipo = "Anillo"
    else:
        print("❌ Diseño no válido")
        return

    HISTORIAL.append({"nombre": nombre, "vms": num_vms, "imagen": "Cirros", "diseño": tipo})
    print("\n✅ Topología desplegada exitosamente 🚀\n")

def ver_historial(usuario, rol):
    carpeta = "/home/ubuntu/proyecto_cloud/topologias"
    archivos = [f for f in os.listdir(carpeta) if f.endswith(".json")]
    
    topologias = []
    for archivo in archivos:
        ruta = os.path.join(carpeta, archivo)
        with open(ruta, "r") as f:
            data = json.load(f)
            # Filtrar según rol
            if rol == "SuperAdministrador" or (rol == "Administrador" and data.get("usuario_creador") == usuario):
                topologias.append(data)

    if not topologias:
        print("\n❌ No hay topologías disponibles para mostrar.")
        return

    print("\n🗂️  ==== Historial de Topologías ====")
    for i, topo in enumerate(topologias):
        vms_count = len(topo.get("vms", []))
        imagen = topo.get("vms", [{}])[0].get("imagen", "N/A") if vms_count > 0 else "N/A"
        print(f"{i+1}. 📌 {topo['nombre']} ({topo['tipo']}) - {vms_count} VMs - {imagen}")

    op = input("\nIngrese el número de la topología para acciones (borrar/unir) o Enter para volver: ").strip()
    if op.isdigit():
        index = int(op) - 1
        if 0 <= index < len(topologias):
            nombre_topo = topologias[index]['nombre']
            print(f"\n🔧 Acciones para topología '{nombre_topo}':")
            print("1. Borrar topología")
            print("2. Unir con otra topología")
            accion = input("Seleccione acción: ").strip()

            if accion == "1":
                eliminar_topologia(nombre_topo)
                # También eliminar el archivo JSON correspondiente
                os.remove(os.path.join(carpeta, f"{nombre_topo}.json"))
                print(f"✅ Topología '{nombre_topo}' borrada.")

            elif accion == "2":
                otro = input("Ingrese número de la otra topología a unir: ").strip()
                if otro.isdigit():
                    otro_index = int(otro) - 1
                    if 0 <= otro_index < len(topologias) and otro_index != index:
                        topo2 = topologias[otro_index]['nombre']
                        vm1 = input(f"Nombre de la VM en '{nombre_topo}' para unir: ")
                        vm2 = input(f"Nombre de la VM en '{topo2}' para unir: ")
                        nombre_nueva = input("Ingrese el nombre de la nueva topología unida: ").strip()
                        unir_topologias(nombre_topo, topo2, vm1, vm2, nombre_nueva)

                        print(f"✅ Topologías '{nombre_topo}' y '{topo2}' unidas.")
                    else:
                        print("❌ Índice no válido o topología duplicada")
                else:
                    print("❌ Entrada inválida")
        else:
            print("❌ Índice no válido")

def ver_recursos():
    print("\n📊 Recursos disponibles:")
    os.system("python3 resource_checker.py")

def ver_logs():
    print("\n📝 ==== Últimos logs de ejecución ====")
    os.system("tail -n 30 /var/log/syslog")

if __name__ == "__main__":
    token = os.environ.get("TOKEN")
    usuario = os.environ.get("USER")
    rol = os.environ.get("ROL")

    if token:
        print(f"Bienvenido {usuario} con rol {rol} 👋")

        while True:
            opcion = menu_principal(usuario, rol, token)

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
            elif opcion == "0":
                print("👋 Saliendo...")
                break
            else:
                print("❌ Opción no válida")
            input("\n🔁 Presione Enter para continuar...")
            clear()
