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
SSH_HOST = "10.20.12.51"
SSH_PORT = 5801
SSH_USER = "ubuntu"  # Usuario para conectar por SSH
SSH_PASSWORD = "pablox123"  # Contraseña para conectar por SSH

# Crear la instancia de FastAPI
app = FastAPI()

# Configuración de hash de contraseñas con bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Función para conectar al servidor y verificar el usuario en la base de datos
def consultar_usuario_en_db(username, password):
    try:
        # Conectar a través de SSH al Server 1
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, port=SSH_PORT, username=SSH_USER, password=SSH_PASSWORD)

        # Consulta SQL para verificar el usuario y la contraseña
        sql_query = f"SELECT * FROM usuarios WHERE user='{username}' AND password='{password}'"
        stdin, stdout, stderr = ssh.exec_command(f"mysql -u root -p -e \"USE mydb; {sql_query}\"")

        # Obtener el resultado de la consulta
        result = stdout.read().decode().strip()

        # Debug: mostrar lo que se obtuvo
        print(f"Resultado de la consulta: {result}")

        ssh.close()

        # Si no hay resultado, las credenciales son incorrectas
        if not result:
            return None

        # Si la consulta devuelve algo, el usuario existe
        return result
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
    password: str

# Endpoint para login y generación del token JWT
@app.post("/login")
def login_for_access_token(form_data: LoginModel):
    # Consultar en la base de datos si el usuario y la contraseña son correctos
    result = consultar_usuario_en_db(form_data.username, form_data.password)
    
    if result is None:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    # Extraer datos del usuario (por ejemplo, rol)
    result_lines = result.split("\n")
    user_data = result_lines[1].split("\t")  # Ajusta esto según la estructura de los resultados
    rol = user_data[2]  # Suponiendo que el rol está en la tercera columna

    # Crear el token JWT
    access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username, "rol": rol}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}
