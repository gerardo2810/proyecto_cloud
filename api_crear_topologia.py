from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import List
from deploy_linear_topology import desplegar_topologia_lineal_from_json
from deploy_ring_topology import desplegar_topologia_anillo_from_json

app = FastAPI()

# Modelo de entrada
class VMConfig(BaseModel):
    cpu: int
    ram: int
    almacenamiento: int
    imagen: str

class TopologiaRequest(BaseModel):
    nombre: str
    tipo: str  # "lineal" o "anillo"
    vms: List[VMConfig]

# Token de prueba
FAKE_VALID_TOKEN = "fake_token_para_prueba"

@app.post("/crear_topologia")
def crear_topologia(request: TopologiaRequest, Authorization: str = Header(...)):
    # Validar formato del token
    if not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Formato de token incorrecto")
    token = Authorization.split(" ")[1]
    if token != FAKE_VALID_TOKEN:
        raise HTTPException(status_code=403, detail="Token inválido")

    # Convertir los datos al formato esperado por las funciones
    payload = {
        "nombre": request.nombre,
        "vms": [vm.dict() for vm in request.vms],
        "imagenes": [vm.imagen for vm in request.vms]
    }

    try:
        if request.tipo == "lineal":
            resultado = desplegar_topologia_lineal_from_json(payload)
        elif request.tipo == "anillo":
            resultado = desplegar_topologia_anillo_from_json(payload)
        else:
            raise HTTPException(status_code=400, detail="Tipo de topología no válido")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al desplegar: {e}")

    return resultado
