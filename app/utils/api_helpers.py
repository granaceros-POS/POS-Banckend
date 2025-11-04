from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

def raise_api_error(message: str, status_code: int = 400):
    """
    Reemplaza la lógica de 'fconfir("E", ...)' para un API.
    """
    logger.warning(f"API Error: {message}")
    raise HTTPException(status_code=status_code, detail=message)