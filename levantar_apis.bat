@echo off
echo 🔐 Iniciando servicio de autenticación...
start cmd /k python -m uvicorn auth_service:app --reload

timeout /t 2

echo 📡 Iniciando servicio de topología...
start cmd /k python -m uvicorn api_crear_topologia:app --reload --port 8001
