from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.utils.common_utils import handle_api_errors
from app.services.venta_service import get_venta_config
from app.models.pos_models import VentaConfigResponse

router = APIRouter()

@router.get("/venta/configuracion", response_model=VentaConfigResponse, tags=["Ventas"])
@handle_api_errors
async def configuracion_venta(
    tipo_venta: int = Query(..., description="Código de tipo de venta (960-964). Corresponde a 'par' en ftitulff."),
    # Estos dos parámetros simulan las variables globales
    # Asumimos que rgp_calm siempre es 1 para la prueba inicial
    # Se incluye rgp_csoc para probar las ramas 'Restaurante' vs 'Distribuidor'
    codigo_almacen: int = Query(1, description="Código de Almacén (grgenera.rgp_calm)"),
    tipo_sociedad: int = Query(1, description="Tipo de Sociedad (grgener1.rgp_csoc, ej: 1=Restaurante, 3=Distribuidor)"),
    prueba_factura: str = Query("N", description="Indicador de prueba de factura (N, S, F). Corresponde a 'gxprufac'."),
    db: Session = Depends(get_db)
):
    """
    Migración de FUNCTION ftitulff. 
    Devuelve la configuración de la venta, incluyendo el tipo de venta (lxitve), 
    el nombre de la venta (lxdes), la descripción de factura (lxdesfac), y la 
    lista de precios (lxnumlis).
    """
    
    return await get_venta_config(
        par=tipo_venta,
        gxprufac=prueba_factura,
        rgp_csoc=tipo_sociedad,
        db=db
    )