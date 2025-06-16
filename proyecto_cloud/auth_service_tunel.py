from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import datetime
from jose import jwt
from passlib.context import CryptContext
import mysql.connector
from custom_logger import registrar_log



# Clave secreta para firmar el JWT
SECRET_KEY = "cloud_grupo2_santivanez_proyecto"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Token expirará en 30 minutos

# Configuración conexión MySQL vía túnel SSH
MYSQL_CONFIG = {
    'host': '127.0.0.1',         # localhost porque usas el túnel SSH
    'port': 53306,               # puerto local redirigido por túnel
    'user': 'usuario',           # usuario MySQL creado
    'password': 'cloud123',      # contraseña MySQL
    'database': 'mydb',          # base de datos
}

# Crear la instancia de FastAPI
app = FastAPI()

# Contexto para hash de contraseñas si decides usar bcrypt (opcional)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Función para conectar a MySQL y verificar usuario y contraseña
def consultar_usuario_en_db(username, contrasenia):
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        sql_query = (
            "SELECT usuarios.user, usuarios.password, roles.rol "
            "FROM usuarios LEFT JOIN roles ON roles.idroles = usuarios.idrol "
            "WHERE usuarios.user = %s AND usuarios.password = %s;"
        )

        cursor.execute(sql_query, (username, contrasenia))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if not result:
            return None

        return list(result)
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Error al conectar con la base de datos: {e}")

# Función para crear el token JWT
def create_access_token(data: dict, expires_delta: datetime.timedelta = None):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + (expires_delta if expires_delta else datetime.timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Modelo de datos para recibir credenciales
class LoginModel(BaseModel):
    username: str
    contrasenia: str

# Endpoint /login que autentica y genera token
@app.post("/login")
def login_for_access_token(form_data: LoginModel):
    result = consultar_usuario_en_db(form_data.username, form_data.contrasenia)

    if result is None:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    username = result[0]
    rol = result[2]

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
