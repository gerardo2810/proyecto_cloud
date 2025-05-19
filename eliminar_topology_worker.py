import subprocess
import re

def run(cmd):
    print(f"➡️ Ejecutando: {cmd}")
    subprocess.run(cmd, shell=True)

print("🧹 Eliminando procesos QEMU (VMs residuales)...")
run("ps aux | grep 'qemu-system' | grep 'vm' | awk '{print $2}' | xargs -r sudo kill -9")

print("🗑️ Borrando discos temporales de VMs...")
run("sudo find /tmp -name 'vm*.qcow2' -delete")

print("🔌 Borrando interfaces TAP tipo 1_XXX y 2_XXX...")

# Obtener todas las interfaces TAP con patrón 1_XXX o 2_XXX
iface_output = subprocess.getoutput("ip -o link show")
for line in iface_output.splitlines():
    match = re.search(r'\d+: (\d+_\d+):', line)
    if match:
        iface = match.group(1)
        run(f"sudo ovs-vsctl --if-exists del-port br-int {iface}")
        run(f"sudo ip link delete {iface} || true")

print("\n✅ Limpieza completa del Worker.")