from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from app.utils.api_helpers import raise_api_error
from fastapi import status
from typing import Literal, Optional
from app.models.pos_models import CajeroData # Necesitamos el modelo del Cajero


async def fcodest_service(
    lxpar: Literal['C', 'P'], 
    lxpa1: int, 
    db: Session
) -> Optional[int]:
    """
    Migración de FUNCTION fcodest(lxpar, lxpa1).
    Busca el código de descripción (dep_cdes) de la operación en dep_descri.
    """
    
    # Esta lógica es una migración directa del SELECT de fcodest en 4GL (dep_descri).
    try:
        query = text("""
            SELECT dep_cdes
            FROM dep_descri
            WHERE dep_tdes = :lxpar
            AND dep_cdes = :lxpa1
        """)
        
        result = db.execute(query, {'lxpar': lxpar, 'lxpa1': lxpa1}).scalar_one_or_none()
        
        # Retornamos el código de operación o None si no se encuentra.
        return result
        
    except Exception as e:
        print(f"Error en fcodest al buscar código {lxpa1}: {e}")
        return None 


async def fverape_service(
    cjp_ccaj: int,        # Código de caja (grrecaja.cjp_ccaj)
    rgp_calm: int,        # Código de almacén (grgenera.rgp_calm)
    gxprufac: str,        # Indicador de prueba (N/F/S)
    db: Session
) -> tuple[bool, str, Optional[CajeroData]]:
    """
    Migración de FUNCTION fverape().
    Verifica si la caja está abierta y si el cajero está asignado.
    
    Returns:
        (bool) Éxito o fracaso, (str) Mensaje de error/éxito, (CajeroData) Datos del cajero.
    """
    
    gxprufac = gxprufac.upper()
    
    # 1. Simulación de Modo de Prueba (gxprufac)
    # IF gxprufac <> "N" THEN ... RETURN (TRUE)
    if gxprufac != "N":
        # Retornamos éxito, simulando la omisión de verificación de BD.
        return True, "Modo de prueba activo.", CajeroData(prp_cper=0, prp_dper="PRUEBA", prp_ccar=0)
    
    # 2. Búsqueda del Código de Apertura (fcodest)
    # LET grrecaja.cjp_iope = fcodest("C", 903)
    cjp_iope_estado = await fcodest_service('C', 903, db) # 903 = Estado de Caja
    
    if cjp_iope_estado is None:
        raise_api_error("El código de operación de caja (903) no está definido en dep_descri.", status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    # 3. Consulta de Registro de Caja (cjp_recaja)
    # Busca la caja que está en estado 'A' (Abierta)
    try:
        query_apertura = text("""
            SELECT cjp_cdin, cjp_ccjr
            FROM cjp_recaja
            WHERE cjp_calm = :rgp_calm
            AND cjp_ccaj = :cjp_ccaj
            AND cjp_iope = :cjp_iope_estado
            AND cjp_iact = 'A' -- "A" de Activa
        """)
        apertura_result = db.execute(query_apertura, {
            'rgp_calm': rgp_calm,
            'cjp_ccaj': cjp_ccaj,
            'cjp_iope_estado': cjp_iope_estado
        }).fetchone()
        
    except Exception as e:
        print(f"Error BD en fverape al buscar cjp_recaja: {e}")
        return False, "Error interno de base de datos.", None
    
    # IF STATUS = NOTFOUND THEN CALL fconfir("E","ESTA CAJA NO TIENE APERTURA")
    if apertura_result is None:
        return False, "ESTA CAJA NO TIENE APERTURA", None

    # Extraer datos:
    cjp_ccjr = apertura_result.cjp_ccjr
    
    # 4. Consulta de Datos del Cajero (prp_person)
    # Busca que el cajero asignado exista y tenga el cargo 2 (Cajero)
    try:
        query_cajero = text("""
            SELECT prp_dper, prp_ccar
            FROM prp_person
            WHERE prp_calm = :rgp_calm
            AND prp_cper = :cjp_ccjr
            AND prp_ccar = 2 -- Código 2 para Cajero (como en tu 4GL)
        """)
        cajero_result = db.execute(query_cajero, {
            'rgp_calm': rgp_calm,
            'cjp_ccjr': cjp_ccjr
        }).fetchone()
        
    except Exception as e:
        print(f"Error BD en fverape al buscar prp_person: {e}")
        return False, "Error interno de base de datos.", None

    # IF STATUS = NOTFOUND THEN CALL fconfir("E","ESTA CAJA NO TIENE CAJERO ASIGNADO")
    if cajero_result is None:
        return False, "ESTA CAJA NO TIENE CAJERO ASIGNADO", None
        
    # Éxito:
    cajero_data = CajeroData(
        prp_cper=cjp_ccjr,
        prp_dper=cajero_result.prp_dper,
        prp_ccar=cajero_result.prp_ccar
    )
    return True, "Caja verificada.", cajero_data