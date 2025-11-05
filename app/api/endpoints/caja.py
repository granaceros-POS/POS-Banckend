from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.utils.common_utils import handle_api_errors
from app.services.caja_service import fverape_service
from app.models.pos_models import CajeroData
from typing import Optional

router = APIRouter()

# El modelo de respuesta final que incluye los datos del Cajero y el código de caja
class CajaVerificacionResponse(CajeroData):
    """Modelo de respuesta para la verificación de caja exitosa."""
    cjp_ccaj: int

@router.get("/caja/verificar_apertura", response_model=Optional[CajaVerificacionResponse], tags=["Caja"])
@handle_api_errors
async def verificar_apertura_caja(
    codigo_caja: int = Query(1, description="Código de la caja a verificar (grrecaja.cjp_ccaj)"),
    codigo_almacen: int = Query(1, description="Código de almacén (grgenera.rgp_calm)"),
    prueba_factura: str = Query("N", description="Indicador de prueba (gxprufac: N, S, F). Omite la verificación si es diferente de 'N'."),
    db: Session = Depends(get_db)
):
    """
    Migración de FUNCTION fverape. 
    Verifica si la caja está abierta y si el cajero asignado existe.
    
    Retorna los datos del cajero si es exitoso, o un error 400 con el mensaje de fallo.
    """
    
    exito, mensaje, cajero_data = await fverape_service(
        cjp_ccaj=codigo_caja,
        rgp_calm=codigo_almacen,
        gxprufac=prueba_factura,
        db=db
    )
    
    if not exito:
        # Si la caja no está abierta o el cajero no está asignado, lanzamos un error.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=mensaje
        )
    
    if cajero_data:
        # La verificación fue exitosa. Devolvemos los datos.
        return CajaVerificacionResponse(
            cjp_ccaj=codigo_caja,
            **cajero_data.model_dump()
        )
    return None