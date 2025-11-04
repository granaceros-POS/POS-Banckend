# --- [DEBUG] Cargando auth.py VERSIÓN SÚPER SIMPLE ---
import sys
print("--- [DEBUG] Cargando auth.py VERSIÓN SÚPER SIMPLE ---", file=sys.stderr)
# --------------------------

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
# --- ¡YA NO IMPORTAMOS verify_password! ---
from app.core.security import create_access_token 
from app.utils.api_helpers import raise_api_error
from app.utils.common_utils import handle_api_errors
from app.db.database import get_db
import logging

# Modelos de datos (siguen igual)
class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

router = APIRouter()
logger = logging.getLogger(__name__)

# --- ¡NUEVA LÓGICA DE USUARIO! ---
# Un solo administrador con clave en texto plano (temporal para desarrollo)
ADMIN_USER = "admin"
ADMIN_PASSWORD = "admin" # ¡Creamos una clave nueva y fácil!

@router.post("/login", response_model=Token, tags=["Autenticación"])
@handle_api_errors
async def login(form_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Endpoint de Login Súper Simple (Temporal)
    """
    logger.info(f"Intento de login para: {form_data.username}")

    # --- ¡NUEVA LÓGICA DE VERIFICACIÓN! ---
    # Comparamos texto plano (inseguro, pero perfecto para desbloquearnos)
    is_user_valid = (form_data.username == ADMIN_USER)
    is_password_valid = (form_data.password == ADMIN_PASSWORD)

    if not (is_user_valid and is_password_valid):
        raise_api_error("Clave o usuario incorrecto", status.HTTP_401_UNAUTHORIZED) 

    # --- Éxito ---
    # Creamos el token de sesión para el admin
    access_token = create_access_token(
        data={"sub": form_data.username, "cargo": "1"} # Cargo 1 = Admin
    )

    logger.info(f"Login exitoso para: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}