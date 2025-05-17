import paramiko

ip = "10.20.12.51"
puerto = 5802
usuario = "ubuntu"
password = "ubuntu"

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, port=puerto, username=usuario, password=password)

    stdin, stdout, stderr = ssh.exec_command("hostname")
    print("✅ HOST:", stdout.read().decode().strip())

    ssh.close()
except Exception as e:
    print("❌ ERROR:", e)
