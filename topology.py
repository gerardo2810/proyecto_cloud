# topology.py

class VM:
    def __init__(self, name, cores, ram, storage, image):
        self.name = name
        self.cores = cores
        self.ram = ram
        self.storage = storage
        self.image = image
        self.connections = []
        self.internet_access = False

    def connect_to(self, other_vm_name):
        if other_vm_name not in self.connections:
            self.connections.append(other_vm_name)

class Topology:
    def __init__(self, name, tipo):
        self.name = name
        self.tipo = tipo
        self.vms = {}

    def add_vm(self, vm):
        self.vms[vm.name] = vm

    def display(self):
        print(f"\nTopología: {self.name} [{self.tipo}]")
        print("-" * 40)
        for vm in self.vms.values():
            for conn in vm.connections:
                print(f"{vm.name} --[enlace]-- {conn}")
