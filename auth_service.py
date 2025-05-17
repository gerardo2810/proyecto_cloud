from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import paramiko
import json
import jose
from jose import JWTError, jwt
from passlib.context import CryptContext
import datetime

# Clave secreta para firmar el JWT
SECRET_KEY = "cloud_grupo2_santivanez_proyecto"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Token expirará en 240 minutos

# Configuración para la conexión SSH
SSH_HOST = "10.20.12.147"
SSH_PORT = 5804
SSH_USER = "ubuntu"  # Usuario para conectar por SSH
SSH_PASSWORD = "ubuntu"  # Contraseña para conectar por SSH

# Crear la instancia de FastAPI
app = FastAPI()

# Configuración de hash de contraseñas con bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Función para conectar al servidor y verificar el usuario en la base de datos
def consultar_usuario_en_db(username, contrasenia):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, port=SSH_PORT, username=SSH_USER, password=SSH_PASSWORD)

        sql_query = (
            f"SELECT usuarios.user, usuarios.password, roles.rol "
            f"FROM usuarios LEFT JOIN roles ON roles.idroles = usuarios.idrol "
            f"WHERE usuarios.user = '{username}' AND usuarios.password = '{contrasenia}';"
        )

        command = f'sqlite3 -separator "|" /home/ubuntu/mydb.db "{sql_query}"'
        stdin, stdout, stderr = ssh.exec_command(command)

        result = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        ssh.close()

        if not result:
            return None

        return result.split("|")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al conectar con la base de datos: {e}")

# Función para crear el token JWT
def create_access_token(data: dict, expires_delta: datetime.timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)  # Default expiration of 15 minutes
    to_encode.update({"exp": expire})  # Añadimos la fecha de expiración
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Modelo de datos para recibir las credenciales del usuario
class LoginModel(BaseModel):
    username: str
    contrasenia: str

@app.post("/login")
def login_for_access_token(form_data: LoginModel):
    result = consultar_usuario_en_db(form_data.username, form_data.contrasenia)

    if result is None:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    username = result[0]  # Ej: 'Pablo'
    rol = result[2]       # Ej: 'SuperAdministrador'

    access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username, "rol": rol}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": username,
        "rol": rol
    }
