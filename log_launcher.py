# Archivo: logger_config.py
import logging
import os

LOG_PATH = "/var/log/pucp_deployer.log"

# Asegurar que existe el archivo con permisos adecuados (solo una vez en setup)
if not os.path.exists(LOG_PATH):
    with open(LOG_PATH, 'w') as f:
        f.write('')
    os.chmod(LOG_PATH, 0o666)

def get_logger():
    logger = logging.getLogger("PUCP_DEPLOYER")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(LOG_PATH)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    # También agregar logging a stderr para debugging en tiempo real (opcional)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger