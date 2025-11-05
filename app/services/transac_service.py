from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from app.utils.api_helpers import raise_api_error
from fastapi import status
from app.models.pos_models import TranInLine


async def ftransac_service(
    data: TranInLine,
    db: Session
) -> bool:
    """
    Migración de FUNCTION ftransac().
    Inserta una línea de transacción idéntica en las tablas trp_tranin y trt_tranin.
    
    Nota: La función ftransac original manejaba la lógica de costos internamente 
    antes de la inserción, aquí asumimos que esos valores (trp_vcos, trp_cospro1, etc.)
    ya vienen calculados en el objeto 'data'.
    """
    
    try:
        # La función ftransac original no usaba una transacción explícita,
        # pero para seguridad en Python/SQLAlchemy, es mejor que las llamadas 
        # a este servicio estén envueltas en un db.begin() / db.commit().
        
        # SQL para la inserción (los 26 campos)
        insert_query = text("""
            INSERT INTO trp_tranin (
                trp_calm, trp_cald, trp_ctran, trp_ftra, trp_cdin, trp_ctor, 
                trp_cdor, trp_cpro, trp_qtra, trp_vpro, trp_vcos, trp_iest, 
                trp_tven, trp_desp, trp_tdes, trp_viva, trp_tiva, trp_nlin, 
                trp_ccom, trp_cnit, trp_cmot, trp_lote, trp_vcto, trp_ccos, 
                trp_cfac, trp_horrec, trp_cospro1, trp_cospro2, trp_cospro3
            ) VALUES (
                :trp_calm, :trp_cald, :trp_ctran, :trp_ftra, :trp_cdin, :trp_ctor, 
                :trp_cdor, :trp_cpro, :trp_qtra, :trp_vpro, :trp_vcos, :trp_iest, 
                :trp_tven, :trp_desp, :trp_tdes, :trp_viva, :trp_tiva, :trp_nlin, 
                :trp_ccom, :trp_cnit, :trp_cmot, :trp_lote, :trp_vcto, :trp_ccos, 
                :trp_cfac, :trp_horrec, :trp_cospro1, :trp_cospro2, :trp_cospro3
            )
        """)
        
        # Convertimos el modelo Pydantic a un diccionario para usarlo como parámetros de SQL
        params = data.model_dump()
        
        # 1. Inserción en la tabla de transacciones actual (trp_tranin)
        db.execute(insert_query, params)
        
        # 2. Inserción en la tabla de transacciones históricas (trt_tranin)
        # Reutilizamos la misma consulta y parámetros, cambiando solo el nombre de la tabla
        insert_query_hist = text(insert_query.text.replace("trp_tranin", "trt_tranin"))
        db.execute(insert_query_hist, params)

        # Nota: ftransac original hacía COMMIT/ROLLBACK fuera de la función; 
        # aquí el commit debe ser manejado por la función que llama a este servicio.
        
        return True
        
    except Exception as e:
        # El 4GL tenía lógica de fibd(2,...) para manejar errores de inserción;
        # Aquí lanzamos una excepción para forzar el ROLLBACK en el nivel superior.
        print(f"Error fatal en ftransac al insertar línea {data.trp_nlin}: {e}")
        raise e