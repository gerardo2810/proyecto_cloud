# topology_manager.py

from topology import VM, Topology
from utils import solicitar_numero, solicitar_opcion

topologies = {}

def crear_topologia():
    nombre = input("Ingrese nombre de la topología: ")
    tipo = input("Ingrese tipo de topología (lineal, malla, árbol, anillo, bus): ")

    topo = Topology(nombre, tipo)
    num_vms = solicitar_numero("¿Cuántas VMs desea crear? ")

    for i in range(num_vms):
        print(f"\nConfigurando VM {i+1}:")
        name = input("Nombre de la VM: ")
        cores = solicitar_numero("Cores: ")
        ram = solicitar_numero("RAM (en MB): ")
        storage = solicitar_numero("Almacenamiento (en GB): ")
        image = input("Imagen (ubuntu, cirros, etc.): ")
        vm = VM(name, cores, ram, storage, image)
        topo.add_vm(vm)

    print("\n--- Configurando conexiones ---")
    for vm_name, vm in topo.vms.items():
        while True:
            otro = input(f"¿A qué VM se conecta {vm_name}? (enter para terminar): ")
            if otro == "":
                break
            if otro in topo.vms and otro != vm_name:
                vm.connect_to(otro)
            else:
                print("Nombre inválido.")

    print("\n--- Definir acceso a Internet ---")
    for vm in topo.vms.values():
        acceso = solicitar_opcion(f"¿{vm.name} debe tener acceso a internet? (s/n): ", ["s", "n"])
        if acceso == "s":
            vm.internet_access = True

    topologies[nombre] = topo
    print(f"\n✅ Topología '{nombre}' creada exitosamente.\n")
    topo.display()

def listar_topologias():
    if not topologies:
        print("No hay topologías creadas.")
        return

    print("\nTopologías existentes:")
    for nombre, topo in topologies.items():
        print(f" - {nombre} ({topo.tipo})")

def borrar_topologia():
    listar_topologias()
    nombre = input("Nombre de la topología a borrar: ")
    if nombre in topologies:
        del topologies[nombre]
        print(f"✅ Topología '{nombre}' eliminada.")
    else:
        print("⚠️ Topología no encontrada.")

def unir_topologias():
    listar_topologias()
    t1 = input("Seleccione primera topología: ")
    t2 = input("Seleccione segunda topología: ")

    if t1 not in topologies or t2 not in topologies:
        print("⚠️ Una o ambas topologías no existen.")
        return

    topo1 = topologies[t1]
    topo2 = topologies[t2]

    print("\nDefina conexiones entre VMs de ambas topologías:")
    for vm1 in topo1.vms:
        for vm2 in topo2.vms:
            decision = solicitar_opcion(f"¿Conectar {vm1} con {vm2}? (s/n): ", ["s", "n"])
            if decision == "s":
                topo1.vms[vm1].connect_to(vm2)
                topo2.vms[vm2].connect_to(vm1)

    # Fusionar topologías
    merged_name = input("Ingrese nombre para la nueva topología unida: ")
    merged_topo = Topology(merged_name, f"{topo1.tipo}+{topo2.tipo}")
    merged_topo.vms = {**topo1.vms, **topo2.vms}

    topologies[merged_name] = merged_topo
    print("\n✅ Topologías unidas exitosamente.\n")
    merged_topo.display()
