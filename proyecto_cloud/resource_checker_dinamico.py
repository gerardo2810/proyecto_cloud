# resource_checker_dinamico.py
import paramiko
import smtplib
import os
from email.mime.text import MIMEText
from custom_logger import registrar_log

usuario = 'ubuntu'
password = 'ubuntu'

CMD = (
    "CPU=$(nproc); "
    "RAM=$(free -m | awk '/Mem:/ {print $7}'); "
    "DISK=$(df / --output=avail -m | tail -1); "
    "echo $CPU $RAM $DISK"
)

def consultar_worker(ip):
    try:
        cliente = paramiko.SSHClient()
        cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        cliente.connect(ip, username=usuario, password=password)
        stdin, stdout, stderr = cliente.exec_command(CMD)
        salida = stdout.read().decode().strip()
        cliente.close()
        cpu, ram, disco = map(int, salida.split())
        return {'cpu': cpu, 'ram': ram, 'almacenamiento': disco}
    except Exception as e:
        registrar_log(f"❌ Error consultando {ip}: {str(e)}")
        return {'cpu': 0, 'ram': 0, 'almacenamiento': 0}

def obtener_recursos(workers):
    recursos = {}
    for nombre, ip in workers.items():
        recursos[nombre] = consultar_worker(ip)
    return recursos

def imprimir_tabla_recursos(recursos):
    print("\n📊 Recursos disponibles por Worker:")
    print("-" * 70)
    print(f"{'Worker':<10} {'CPU (núcleos)':<15} {'RAM (MB)':<15} {'Disco (MB)':<15}")
    print("-" * 70)
    for nombre, datos in recursos.items():
        print(f"{nombre:<10} {datos['cpu']:<15} {datos['ram']:<15} {datos['almacenamiento']:<15}")
    print("-" * 70)

def enviar_correo_resumen(recursos):
    cuerpo = "📊 Recursos disponibles por Worker:\n\n"
    cuerpo += f"{'Worker':<10} {'CPU':<10} {'RAM':<10} {'Disco':<10}\n"
    cuerpo += "-" * 45 + "\n"
    for nombre, datos in recursos.items():
        cuerpo += f"{nombre:<10} {datos['cpu']:<10} {datos['ram']:<10} {datos['almacenamiento']:<10}\n"
    
    remitente = "telecompucp39@gmail.com"
    destinatario = "a20206089@pucp.edu.pe"
    asunto = "📈 Reporte de recursos disponibles en Workers"
    password_email = "udxg stwu xmbc ajii"  # Usa clave de aplicación, no contraseña real

    msg = MIMEText(cuerpo)
    msg['Subject'] = asunto
    msg['From'] = remitente
    msg['To'] = destinatario

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(remitente, password_email)
            server.sendmail(remitente, destinatario, msg.as_string())
        print("📤 Correo enviado correctamente al SuperAdministrador.")
    except Exception as e:
        print(f"❌ Error enviando correo: {e}")
        registrar_log(f"❌ Error enviando correo: {str(e)}")
# Al final de resource_checker_dinamico.py
def ejecutar_reporte_recursos():
    workers = {
        "worker1": "10.0.10.2",
        "worker2": "10.0.10.3",
        "worker3": "10.0.10.4"
    }
    recursos = obtener_recursos(workers)
    imprimir_tabla_recursos(recursos)
    enviar_correo_resumen(recursos)


if __name__ == "__main__":
    workers = {
        "worker1": "10.0.10.2",
        "worker2": "10.0.10.3",
        "worker3": "10.0.10.4"
    }
    recursos = obtener_recursos(workers)
    imprimir_tabla_recursos(recursos)
    enviar_correo_resumen(recursos)
