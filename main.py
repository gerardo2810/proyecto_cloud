import os
import sys
import getpass
import time
import json
from deploy_linear_topology import desplegar_topologia_lineal
from deploy_ring_topology import desplegar_topologia_anillo
from unir_topologia import unir_topologias
from eliminar_topologia import eliminar_topologia

HISTORIAL = []
USUARIOS = {
    "admin": {"password": "admin123", "rol": "Administrador"},
    "super": {"password": "super123", "rol": "Superadministrador"},
}

IMAGENES = {
    "1": "cirros-0.5.1-x86_64-disk.img",
    "2": "ubuntu-server-22.04.img"
}

def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

def login():
    clear()
    print("""
██████╗ ██╗   ██╗ ██████╗██████╗ ██████╗ ███████╗██████╗ ██╗     ███████╗██╗   ██╗
██╔══██╗██║   ██║██╔════╝██╔══██╗██╔══██╗██╔════╝██╔══██╗██║     ██╔════╝╚██╗ ██╔╝
██████╔╝██║   ██║██║     ██████╔╝██║  ██║█████╗  ██████╔╝██║     █████╗   ╚████╔╝ 
██╔═══╝ ██║   ██║██║     ██╔═══╝ ██║  ██║██╔══╝  ██╔═══╝ ██║     ██╔══╝    ╚██╔╝  
██║     ╚██████╔╝╚██████╗██║     ██████╔╝███████╗██║     ███████╗███████╗   ██║   
╚═╝      ╚═════╝  ╚═════╝╚═╝     ╚═════╝ ╚══════╝╚═╝     ╚══════╝╚══════╝   ╚═╝   
    """)
    print("==== Bienvenido a PUCPDEPLOY ====")
    usuario = input("👤 Usuario: ")
    clave = getpass.getpass("🔐 Contraseña: ")
    if usuario in USUARIOS and USUARIOS[usuario]["password"] == clave:
        print(f"\n✅ Acceso concedido como {USUARIOS[usuario]['rol']}\n")
        return usuario, USUARIOS[usuario]["rol"]
    print("\n❌ Credenciales incorrectas.\n")
    sys.exit(1)

def menu_principal():
    print("1️⃣  Crear Topología")
    print("2️⃣  Historial de topologías")
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

def crear_topologia():
    nombre = input("\n📛 Nombre de la topología (solo letras y números): ").strip()
    if not nombre.isalnum():
        print("❌ Nombre no válido. Solo letras y números sin espacios.")
        return

    print("\n1. Crear VMs con Flavors\n2. Crear VMs una por una")
    modo = input("Seleccione un modo: ")

    num_vms = input_num("🔢 Cantidad de VMs (2-4): ")
    if num_vms < 2 or num_vms > 4:
        print("❌ Solo se permiten entre 2 y 4 VMs")
        return

    vms = []
    for i in range(num_vms):
        print(f"\n🖥️  Configuración de VM{i+1}")
        cpu = input_num("⚙️  CPU: ")
        ram = input_num("📦 RAM (MB): ")
        disco = input_num("💾 Almacenamiento (MB): ")
        print("📂 Imagen disponible:")
        print("1. Cirros")
        print("2. Ubuntu")
        img_sel = input("Seleccione imagen base (1/2): ")
        if img_sel not in IMAGENES:
            print("❌ Imagen no válida, se usará Cirros por defecto")
            img_sel = "1"
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
    print("\n🗂️  ==== Historial de Topologías ====")
    for i, topo in enumerate(HISTORIAL):
        print(f"{i+1}. 📌 {topo['nombre']} ({topo['diseño']}) - {topo['vms']} VMs - {topo['imagen']}")

    op = input("\nIngrese el número de la topología para acciones (borrar/unir) o Enter para volver: ").strip()
    if op.isdigit():
        index = int(op) - 1
        if 0 <= index < len(HISTORIAL):
            nombre_topo = HISTORIAL[index]['nombre']
            print(f"\n🔧 Acciones para topología '{nombre_topo}':")
            print("1. Borrar topología")
            print("2. Unir con otra topología")
            accion = input("Seleccione acción: ").strip()

            if accion == "1":
                eliminar_topologia(nombre_topo)
                print(f"✅ Topología '{nombre_topo}' borrada.")
                HISTORIAL.pop(index)

            elif accion == "2":
                otro = input("Ingrese número de la otra topología a unir: ")
                if otro.isdigit():
                    otro_index = int(otro) - 1
                    if 0 <= otro_index < len(HISTORIAL) and otro_index != index:
                        topo2 = HISTORIAL[otro_index]['nombre']
                        vm1 = input(f"Nombre de la VM en '{nombre_topo}' para unir: ")
                        vm2 = input(f"Nombre de la VM en '{topo2}' para unir: ")
                        unir_topologias(str(index+1), str(otro_index+1), vm1, vm2)
                        print(f"✅ Topologías '{nombre_topo}' y '{topo2}' unidas.")
                    else:
                        print("❌ Índice no válido o topología duplicada")
                else:
                    print("❌ Entrada inválida")


def ver_recursos():
    print("\n📊 Recursos disponibles:")
    os.system("python3 resource_checker.py")

def ver_logs():
    print("\n📝 ==== Últimos logs de ejecución ====")
    os.system("tail -n 30 /var/log/syslog")

if __name__ == "__main__":
    usuario, rol = login()
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
        elif opcion == "0":
            print("👋 Saliendo...")
            break
        else:
            print("❌ Opción no válida")
        input("\n🔁 Presione Enter para continuar...")
        clear()
