import os
import sys
import requests
import getpass
import time
import json
from unir_topologia import unir_topologias
from eliminar_topologia import eliminar_topologia

# URL del microservicio de autenticación
HISTORIAL = []
AUTH_SERVICE_URL = "http://127.0.0.1:8000/login"
TOPOLOGY_SERVICE_URL = "http://127.0.0.1:8001/crear_topologia"

IMAGENES = {
    "1": "cirros-0.5.1-x86_64-disk.img",
    "2": "ubuntu-server-22.04.img"
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
            token = response.json()["access_token"]
            print(f"\n✅ Acceso concedido. Token recibido.")
            return token
        else:
            intentos -= 1
            print(f"\n❌ Credenciales incorrectas. Quedan {intentos} intento(s).\n")

    print("\n❌ Se agotaron los intentos. Programa terminado.\n")
    sys.exit(1)

def menu_principal(token):
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

def crear_topologia(token):
    while True:
        nombre = input("\n📛 Nombre de la topología (solo letras y números): ").strip()
        if not nombre.isalnum():
            print("❌ Nombre no válido. Solo letras y números sin espacios.")
            continue
        break

    num_vms = input_num("🔢 Cantidad de VMs (2-4): ")
    if num_vms < 2 or num_vms > 4:
        print("❌ Solo se permiten entre 2 y 4 VMs")
        return

    vms = []
    for i in range(num_vms):
        print(f"\n🖥️  Configuración de VM{i+1}")
        print("📂 Imagen:")
        print("1. Cirros")
        print("2. Ubuntu")
        while True:
            img_sel = input("Seleccione imagen (1/2): ")
            if img_sel in IMAGENES:
                break
            print("❌ Imagen inválida.")

        if img_sel == "1":
            while True:
                cpu = input_num("⚙️  CPU: ")
                if validar_cirros_cpu(cpu):
                    break
                print("❌ CPU para Cirros debe ser exactamente 1")
            while True:
                ram = input_num("📦 RAM (MB): ")
                if validar_cirros_rango(ram):
                    break
                print("❌ RAM debe estar entre 300 y 700")
            while True:
                disco = input_num("💾 Almacenamiento (MB): ")
                if validar_cirros_rango(disco):
                    break
                print("❌ Almacenamiento debe estar entre 300 y 700")
        else:
            cpu = input_num("⚙️  CPU: ")
            ram = input_num("📦 RAM (MB): ")
            disco = input_num("💾 Almacenamiento (MB): ")

        vms.append({
            "cpu": cpu,
            "ram": ram,
            "almacenamiento": disco,
            "imagen": IMAGENES[img_sel]
        })

    print("\n🔗 Seleccione diseño de topología:")
    print("1. Lineal")
    print("2. Anillo")
    diseno = input("Diseño: ")
    tipo = "lineal" if diseno == "1" else "anillo" if diseno == "2" else None

    if not tipo:
        print("❌ Diseño inválido")
        return

    data = {
        "nombre": nombre,
        "tipo": tipo,
        "vms": vms
    }

    try:
        res = requests.post(
            TOPOLOGY_SERVICE_URL,
            headers={"Authorization": f"Bearer {token}"},
            json=data
        )
        if res.status_code == 200:
            print("✅ Topología desplegada exitosamente 🚀")
            HISTORIAL.append({"nombre": nombre, "vms": num_vms, "imagen": "Cirros", "diseño": tipo.capitalize()})
        else:
            print(f"❌ Error al desplegar: {res.status_code} → {res.text}")
    except Exception as e:
        print(f"❌ Fallo de conexión con el microservicio: {e}")

def ver_historial(token):
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


def ver_recursos(token):
    print("\n📊 Recursos disponibles:")
    os.system("python3 resource_checker.py")

def ver_logs(token):
    print("\n📝 ==== Últimos logs de ejecución ====")
    os.system("tail -n 30 /var/log/syslog")

if __name__ == "__main__":
    token = login()
    while True:
        opcion = menu_principal(token)
        if opcion == "1":
            crear_topologia(token)
        elif opcion == "2":
            ver_historial(token)
        elif opcion == "3":
            ver_recursos(token)
        elif opcion == "4":
            ver_logs(token)
        elif opcion == "0":
            print("👋 Saliendo...")
            break
        else:
            print("❌ Opción no válida")
        input("\n🔁 Presione Enter para continuar...")
        clear()