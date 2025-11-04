import functools
import sys
import logging
from app.utils.api_helpers import raise_api_error
from fastapi import HTTPException

logger = logging.getLogger(__name__)

def handle_api_errors(func):
    """
    Decorador que reemplaza 'WHENEVER ERROR CALL fwhene' 
    para endpoints de API.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            # Soporta funciones 'async' de FastAPI
            return await func(*args, **kwargs)
        except HTTPException as http_exc:
            # Si ya es un error de API, solo lo relanza
            raise http_exc
        except Exception as e:
            # Si es un error inesperado, lo loguea
            logger.exception(f"Error inesperado en {func.__name__}")
            # Y devuelve un error 500 genérico
            raise HTTPException(status_code=500, detail=f"Error interno: {e}")
    return wrapper