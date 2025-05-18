import json
import os

FLAVOR_FILE = "flavors.json"

# Valores por defecto si no existe el archivo
DEFAULT_FLAVORS = {
    "cirros": {
        "vcpus": 1,
        "ram": 512,         # en MB
        "disk": 1           # en GB
    },
    "ubuntu": {
        "vcpus": 1,
        "ram": 512,
        "disk": 2.2
    }
}

def cargar_flavors():
    if not os.path.exists(FLAVOR_FILE):
        guardar_flavors(DEFAULT_FLAVORS)
        return DEFAULT_FLAVORS
    with open(FLAVOR_FILE, "r") as f:
        return json.load(f)

def guardar_flavors(flavors):
    with open(FLAVOR_FILE, "w") as f:
        json.dump(flavors, f, indent=4)

def listar_flavors():
    return cargar_flavors()

def obtener_flavor(nombre):
    flavors = cargar_flavors()
    return flavors.get(nombre)

def agregar_flavor(nombre, vcpus, ram, disk):
    flavors = cargar_flavors()
    if nombre in flavors:
        raise ValueError(f"Flavor '{nombre}' ya existe.")
    flavors[nombre] = {"vcpus": vcpus, "ram": ram, "disk": disk}
    guardar_flavors(flavors)

def eliminar_flavor(nombre):
    flavors = cargar_flavors()
    if nombre not in flavors:
        raise ValueError(f"Flavor '{nombre}' no existe.")
    del flavors[nombre]
    guardar_flavors(flavors)

# Solo para pruebas
if __name__ == "__main__":
    print("📦 Flavors actuales:")
    for nombre, data in listar_flavors().items():
        print(f"{nombre}: {data}")