from app.models.pos_models import VentaConfigResponse
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from app.utils.api_helpers import raise_api_error
from fastapi import status
from typing import Literal

# --- Constantes para la lógica de ftitulff ---
# Corresponde a grgener1.rgp_csoc
RGPC_SOC_DISTRIBUIDOR_MODE = 3 

async def get_venta_config(
    par: int,
    gxprufac: str,
    rgp_csoc: int,
    db: Session
) -> VentaConfigResponse:
    """
    Migración de la lógica principal de FUNCTION ftitulff.
    Determina el tipo de venta (lxitve) y el nombre (lxdes) basado en el código (par).
    """
    
    lxdes, lxdesfac, lxitve, lxnumlis = "", "", 0, 0
    
    # 4GL usa mayúsculas para la comparación de indicadores
    gxprufac = gxprufac.upper()
    
    # Lógica CASE de ftitulff (recreada con Python match/case)
    match par:
        case 960:
            lxitve = 960
            if rgp_csoc != RGPC_SOC_DISTRIBUIDOR_MODE:
                lxdes, lxdesfac = 'DRIVE', 'DRIVE'
            else:
                lxdes, lxdesfac = 'INSTITUCIONA', 'PARA LLEVAR INSTITUC'
        
        case 961:
            lxitve = 961
            if rgp_csoc != RGPC_SOC_DISTRIBUIDOR_MODE:
                if gxprufac == "F": # WHEN gxprufac = "F" THEN LET lxdes='CORTESIA'
                    lxdes, lxdesfac = 'CORTESIA', 'PARA LA MESA' 
                else:
                    # En tu 4GL se evalúa giopcmes (lo simplificamos aquí como 'MESA')
                    lxdes, lxdesfac = 'MESA', 'PARA LA MESA' 
            else:
                lxdes, lxdesfac = 'DISTRI/SUPER', 'PARA LLEVAR DISTRIBUI'
                
        case 962:
            lxitve = 962
            lxdes, lxdesfac = 'DOMICILIO', 'DOMICILIO'
            
        case 963:
            lxitve = 963
            if rgp_csoc != RGPC_SOC_DISTRIBUIDOR_MODE:
                if gxprufac == "F": # WHEN gxprufac = "F" THEN LET lxdes='VENTA'
                    lxdes, lxdesfac = 'VENTA', 'PARA LLEVAR'
                else:
                    lxdes, lxdesfac = 'LLEVAR', 'PARA LLEVAR'
            else:
                lxdes, lxdesfac = 'PUBLICO', 'PARA LLEVAR PUBLICO'
                
        case 964:
            lxitve = 964
            if rgp_csoc != RGPC_SOC_DISTRIBUIDOR_MODE:
                lxdes, lxdesfac = 'DESCUENTO', 'PARA LA MESA'
            else:
                lxdes, lxdesfac = 'DISTRIBUIDO', 'PARA LLEVAR DISTRIBUI'
                
        case _:
            # Si el código no está en el CASE, devuelve error
            raise_api_error("Código de tipo de venta no válido (par).", status.HTTP_400_BAD_REQUEST)

    # 4GL: Determinar la Lista de Precios (lxnumlis)
    # Esto simula el SELECT tip_clis INTO lxnumlis FROM tip_tipven WHERE tip_tven = lxitve
    
    # Nota: Tu código 4GL hace esta consulta tanto para rgp_csoc <> 3 como para rgp_csoc == 3
    # (Excepto para la lógica especial de lxindfac="3" y lxnumlis=0, que omitiremos por complejidad inicial)
    
    try:
        query = text("""
            SELECT tip_clis
            FROM tip_tipven
            WHERE tip_tven = :lxitve
        """)
        # Ejecutamos la consulta a la base de datos
        result = db.execute(query, {'lxitve': lxitve}).scalar_one_or_none()
        
        # Asignamos el valor, o 0 si no se encuentra
        lxnumlis = result if result is not None else 0
        
    except Exception as e:
        # En caso de error de conexión o consulta, asumimos lista 0 y registramos el error.
        print(f"Error en BD al buscar Lista de Precios para {lxitve}: {e}")
        lxnumlis = 0


    return VentaConfigResponse(
        lxitve=lxitve,
        lxdes=lxdes,
        lxdesfac=lxdesfac,
        lxnumlis=lxnumlis,
        gxprufac=gxprufac
    )