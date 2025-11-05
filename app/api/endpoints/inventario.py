from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.utils.common_utils import handle_api_errors
from app.services.inventario_service import finvpro_service, fdesglos_service
from app.models.pos_models import InvProResult
from decimal import Decimal
from typing import Tuple

router = APIRouter()

class DesglosResult(BaseModel):
    """Modelo de respuesta para el desglose de recetas."""
    costo_materia_prima: float
    costo_suministros: float
    costo_mano_obra: float
    cantidad_vendida: float
    codigo_producto: int
    
    
@router.post("/inventario/desglose_venta", response_model=DesglosResult, tags=["Inventario"])
@handle_api_errors
async def procesar_desglose_venta(
    codigo_producto: int = Query(..., description="Código del producto (lxcpro)"),
    cantidad: float = Query(..., description="Cantidad a vender (licantid)"),
    tipo_venta: int = Query(961, description="Tipo de Venta (lxtven, ej: 961=Mesa)"),
    codigo_almacen: int = Query(1, description="Código de almacén (rgp_calm)"),
    incluir_suministros: str = Query('S', description="Incluir suministros en el desglose (lxincsum: S/N)"),
    db: Session = Depends(get_db)
):
    """
    Migración de FUNCTION fdesglos. 
    Procesa la venta de una receta o producto final, resta recursivamente 
    todos los ingredientes del inventario (vía finvpro) y calcula el costo total.
    """
    
    licantid_decimal = Decimal(str(cantidad))
    
    # Llama al servicio que maneja la recursividad
    costo_totales: Tuple[Decimal, Decimal, Decimal] = await fdesglos_service(
        db=db,
        lxcpro=codigo_producto,
        licantid=licantid_decimal,
        lxtven=tipo_venta,
        rgp_calm=codigo_almacen,
        lxincsum=incluir_suministros
    )
    
    # Retornar los costos
    return DesglosResult(
        costo_materia_prima=float(costo_totales[0]),
        costo_suministros=float(costo_totales[1]),
        costo_mano_obra=float(costo_totales[2]),
        cantidad_vendida=cantidad,
        codigo_producto=codigo_producto
    )

    
@router.post("/inventario/actualizar", response_model=InvProResult, tags=["Inventario"])
@handle_api_errors
async def actualizar_inventario(
    codigo_producto: int = Query(..., description="Código del producto (lxcpro)"),
    cantidad_movida: float = Query(..., description="Cantidad a mover (lxcannue)"),
    # lxmodulo: -1 para Venta/Salida, 1 para Entrada/Compra
    modulo: int = Query(-1, description="Módulo de movimiento (-1=Salida/Venta, 1=Entrada/Compra)"),
    codigo_almacen: int = Query(1, description="Código de almacén (rgp_calm)"),
    calcula_costo: str = Query('S', description="Calcular costo promedio (licalcos: S/N)"),
    db: Session = Depends(get_db)
):
    """
    Migración de FUNCTION finvpro. (Se mantiene para ajustes manuales y pruebas)
    Actualiza la cantidad de inventario y recalcula el costo promedio usando transacciones.
    """
    
    # El servicio espera Decimal para precisión
    lxcannue_decimal = Decimal(str(cantidad_movida))
    
    # El servicio espera el parámetro lxpar como 'A' o 'E' 
    lxpar_literal = 'A' if modulo > 0 else 'E' 
    
    return await finvpro_service(
        lxcpro=codigo_producto,
        lxcannue=lxcannue_decimal,
        lxmodulo=modulo,
        rgp_calm=codigo_almacen,
        db=db,
        lxpar=lxpar_literal,
        licalcos=calcula_costo
    )