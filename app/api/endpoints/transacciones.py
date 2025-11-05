from fastapi import APIRouter, Depends, status, HTTPException # <-- ¡HTTPException CORREGIDO!
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.utils.common_utils import handle_api_errors
from app.services.transac_service import ftransac_service
from app.models.pos_models import TranInLine
from decimal import Decimal
from typing import List
from datetime import date

router = APIRouter()

# Modelo de respuesta simple para confirmar la inserción
class TranInResponse(BaseModel):
    success: bool
    message: str
    num_lineas: int = 1


@router.post("/transacciones/registrar_linea", response_model=TranInResponse, tags=["Transacciones"])
@handle_api_errors
async def registrar_linea_transaccion(
    linea_data: TranInLine,
    db: Session = Depends(get_db)
):
    """
    Migración de FUNCTION ftransac. 
    Registra una línea de transacción completa en trp_tranin y trt_tranin.
    """
    
    try:
        # Nota: Asumimos que esta llamada a ftransac_service no necesita un db.begin() 
        # porque la transacción final (db.commit()) se hace después.
        exito = await ftransac_service(data=linea_data, db=db)
        
        # Hacemos el commit final (que en el 4GL era externo)
        db.commit()

        if exito:
            return TranInResponse(
                success=True,
                message="Línea de transacción registrada correctamente.",
                num_lineas=1
            )
        else:
             raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Fallo al registrar la línea de transacción en la base de datos."
            )
            
    except Exception as e:
        db.rollback() # Aseguramos el rollback si algo falló en la base de datos
        # El error de la BD será atrapado aquí y devuelto como 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fatal durante la inserción: {e}"
        )