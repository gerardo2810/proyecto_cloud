import os
import sys
import getpass
import json
from deploy_linear_topology import desplegar_topologia_lineal
from deploy_ring_topology import desplegar_topologia_anillo
from unir_topologia import unir_topologias
from eliminar_topologia import eliminar_topologia
from flavors_manager import obtener_flavor, listar_flavors

HISTORIAL = []
USUARIOS = {
    "admin": {"password": "admin123", "rol": "Administrador"},
    "super": {"password": "super123", "rol": "Superadministrador"},
}

IMAGENES = {
    "1": {"nombre": "cirros-0.5.1-x86_64-disk.img", "flavor": "cirros"},
    "2": {"nombre": "ubuntu-server-22.04.img", "flavor": "ubuntu"}
}

def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

def input_num(msg):
    while True:
        val = input(msg)
        if val.isdigit():
            return int(val)
        print("❗ Ingrese solo números.")

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
    print("==== Bienvenido a PUCPDEPLOYER ====")

    intentos = 3
    while intentos > 0:
        usuario = input("👤 Usuario: ")
        clave = getpass.getpass("🔐 Contraseña: ")
        if usuario in USUARIOS and USUARIOS[usuario]["password"] == clave:
            print(f"\n✅ Acceso concedido como {USUARIOS[usuario]['rol']}\n")
            return usuario, USUARIOS[usuario]["rol"]
        intentos -= 1
        print(f"\n❌ Credenciales incorrectas. Quedan {intentos} intentos.\n")

    print("\n❌ Se agotaron los intentos. Programa terminado.\n")
    sys.exit(1)

def crear_vm_manual(idx):
    print(f"\n🖥️  Configuración de VM{idx+1} (Modo Manual)")
    print("📂 Imagen disponible:")
    for key, data in IMAGENES.items():
        print(f"{key}. {data['nombre']}")
    while True:
        img_sel = input("Seleccione imagen base (1/2): ")
        if img_sel in IMAGENES:
            break
        print("❌ Imagen no válida. Seleccione 1 o 2.")

    if img_sel == "1":
        while True:
            cpu = input_num("⚙️  CPU: ")
            if cpu == 1:
                break
            print("❌ Para Cirros, CPU debe ser 1")
        while True:
            ram = input_num("📦 RAM (MB): ")
            if 300 <= ram <= 700:
                break
            print("❌ RAM para Cirros debe estar entre 300 y 700 MB")
        while True:
            disco = input_num("💾 Almacenamiento (MB): ")
            if 300 <= disco <= 700:
                break
            print("❌ Disco para Cirros debe estar entre 300 y 700 MB")
    else:
        cpu = input_num("⚙️  CPU: ")
        ram = input_num("📦 RAM (MB): ")
        disco = input_num("💾 Almacenamiento (MB): ")

    imagen = IMAGENES[img_sel]["nombre"]
    return (cpu, ram, disco, imagen)

def crear_vm_por_flavor(idx, flavors):
    print(f"\n🖥️  VM{idx+1} - Selección de Flavor")
    flavor_keys = list(flavors.keys())

    for i, (nombre_flavor, spec) in enumerate(flavors.items(), 1):
        print(f"{i}. {nombre_flavor}: {spec['vcpus']} CPU, {spec['ram']}MB RAM, {spec['disk']}GB Disco")

    while True:
        fsel = input(f"Seleccione flavor (1-{len(flavor_keys)}): ")
        if fsel.isdigit() and 1 <= int(fsel) <= len(flavor_keys):
            break
        print("❌ Selección inválida.")

    flavor_name = flavor_keys[int(fsel) - 1]
    flavor = obtener_flavor(flavor_name)

    print("📂 Imagen disponible:")
    for key, data in IMAGENES.items():
        print(f"{key}. {data['nombre']}")
    while True:
        img_sel = input("Seleccione imagen base (1/2): ")
        if img_sel in IMAGENES:
            break
        print("❌ Imagen no válida.")

    imagen = IMAGENES[img_sel]["nombre"]
    return (flavor["vcpus"], flavor["ram"], flavor["disk"], imagen)

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
    if modo == "1":
        flavors = listar_flavors()
        for i in range(num_vms):
            vms.append(crear_vm_por_flavor(i, flavors))
    elif modo == "2":
        for i in range(num_vms):
            vms.append(crear_vm_manual(i))
    else:
        print("❌ Modo inválido")
        return

    print("\n🔗 Seleccione diseño de topología:")
    print("1. Lineal")
    print("2. Anillo")
    diseno = input("Diseño: ")

    imagenes = [img for (_, _, _, img) in vms]
    vms_info = [(cpu, ram, disco) for (cpu, ram, disco, _) in vms]

    print("\n⚙️  Desplegando topología...\n")
    if diseno == "1":
        desplegar_topologia_lineal(nombre, vms_info, imagenes)
        tipo = "Lineal"
    elif diseno == "2":
        desplegar_topologia_anillo(nombre, vms_info, imagenes)
        tipo = "Anillo"
    else:
        print("❌ Diseño no válido")
        return

    HISTORIAL.append({"nombre": nombre, "vms": num_vms, "imagen": "Flavors" if modo == "1" else "Manual", "diseño": tipo})
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
                HISTORIAL.pop(index)
                print(f"✅ Topología '{nombre_topo}' borrada.")

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

def ver_flavors():
    print("\n📦 Flavors disponibles:")
    flavors = listar_flavors()
    for nombre, specs in flavors.items():
        print(f"- {nombre}: {specs['vcpus']} CPU, {specs['ram']}MB RAM, {specs['disk']}GB Disco")

def ver_logs():
    print("\n📝 ==== Últimos logs de ejecución ====")
    os.system("tail -n 30 /var/log/syslog")

def menu_principal():
    print("\n📋 Menú Principal")
    print("1️⃣  Crear Topología")
    print("2️⃣  Ver Historial de Topologías")
    print("3️⃣  Ver Recursos de Servidores")
    print("4️⃣  Ver Flavors Disponibles")
    print("5️⃣  Ver Logs")
    print("0️⃣  Salir")
    return input("\nSeleccione una opción: ")

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
            ver_flavors()
        elif opcion == "5":
            ver_logs()
        elif opcion == "0":
            print("👋 Saliendo...")
            break
        else:
            print("❌ Opción no válida")
        input("\n🔁 Presione Enter para continuar...")
        clear()
