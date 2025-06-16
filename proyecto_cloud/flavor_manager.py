# Nombre: flavor_manager.py
import json
import os
from custom_logger import registrar_log

FLAVORS_FILE = "/home/ubuntu/proyecto_cloud/flavors.json"

def cargar_flavors():
    if not os.path.exists(FLAVORS_FILE):
        return {}
    with open(FLAVORS_FILE, "r") as f:
        return json.load(f)

def guardar_flavors(flavor_data):
    with open(FLAVORS_FILE, "w") as f:
        json.dump(flavor_data, f, indent=2)

def crear_flavor(nombre, cpu, ram, disco, imagen, usuario, rol):
    flavors = cargar_flavors()
    if nombre in flavors:
        print(f"❌ El flavor '{nombre}' ya existe.")
        return False
    flavors[nombre] = {
        "cpu": cpu,
        "ram": ram,
        "disco": disco,
        "imagen": imagen,
        "usuario_creador": usuario,
        "rol_creador": rol
    }
    guardar_flavors(flavors)
    print(f"✅ Flavor '{nombre}' creado correctamente.")
    return True

def listar_flavors(usuario, rol):
    flavors = cargar_flavors()
    if not flavors:
        print("⚠️ No hay flavors definidos.")
        return

    print("\n📦 Flavors disponibles:")
    print("-" * 90)
    print(f"{'Nombre':<20} {'CPU':<5} {'RAM (MB)':<10} {'Disco (MB)':<12} {'Imagen':<30} Creador")
    print("-" * 90)

    mostrados = 0
    for nombre, datos in flavors.items():
        if rol == "SuperAdministrador" or datos.get("usuario_creador") == usuario:
            print(f"{nombre:<20} {datos['cpu']:<5} {datos['ram']:<10} {datos['disco']:<12} {datos['imagen']:<30} {datos.get('usuario_creador', 'N/A')}")
            mostrados += 1

    if mostrados == 0:
        print("⚠️ No hay flavors visibles para tu usuario.")
    print("-" * 90)

def obtener_flavor(nombre):
    return cargar_flavors().get(nombre)

def eliminar_flavor(nombre, usuario=None, rol=None):
    flavors = cargar_flavors()
    if nombre not in flavors:
        print(f"❌ El flavor '{nombre}' no existe.")
        return

    creador = flavors[nombre].get("usuario_creador")
    if rol != "SuperAdministrador" and creador != usuario:
        print("❌ No tienes permisos para eliminar este flavor.")
        return

    del flavors[nombre]
    guardar_flavors(flavors)
    print(f"✅ Flavor '{nombre}' eliminado.")

def editar_flavor(nombre, cpu=None, ram=None, disco=None, imagen=None, usuario=None, rol=None):
    flavors = cargar_flavors()

    if nombre not in flavors:
        print(f"❌ El flavor '{nombre}' no existe.")
        return

    creador = flavors[nombre].get("usuario_creador")
    if rol != "SuperAdministrador" and creador != usuario:
        print("❌ No tienes permisos para editar este flavor.")
        return

    if cpu is not None:
        flavors[nombre]['cpu'] = cpu
    if ram is not None:
        flavors[nombre]['ram'] = ram
    if disco is not None:
        flavors[nombre]['disco'] = disco
    if imagen is not None:
        flavors[nombre]['imagen'] = imagen

    guardar_flavors(flavors)
    print(f"✅ Flavor '{nombre}' actualizado.")