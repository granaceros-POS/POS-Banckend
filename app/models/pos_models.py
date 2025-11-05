from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal
from datetime import date

# --- Modelos de Estructuras de Datos Generales y Respuestas ---

class GeneraModel(BaseModel):
    """Simula campos de grgenera y grgener1."""
    rgp_calm: int = 0
    rgp_demp: Optional[str] = None
    rgp_isok: Optional[str] = "N"
    rgp_csoc: Optional[int] = 0
    
class CajeroData(BaseModel):
    """Estructura de datos del Cajero obtenida de prp_person."""
    prp_cper: int       # Código de personal/cajero (grrecaja.cjp_ccjr)
    prp_dper: str       # Nombre del cajero (prp_person.prp_dper)
    prp_ccar: int       # Código de cargo (prp_person.prp_ccar, debe ser 2)
    
class VentaConfigResponse(BaseModel):
    """Modelo de respuesta para la configuración de venta (ftitulff)."""
    lxitve: int
    lxdes: str
    lxdesfac: str
    lxnumlis: int
    
    # Campo de validación adicional
    gxprufac: Optional[str] = "N"
    
class InvProResult(BaseModel):
    """Resultado de finvpro: Nuevo costo y tipo de producto."""
    lxcosnue: Decimal
    lxtippro: int

class TranInLine(BaseModel):
    """
    Modelo que representa los 26 campos de la línea de transacción (ftransac).
    Corresponde a la fila completa insertada en trp_tranin y trt_tranin.
    """
    trp_calm: int
    trp_cald: int
    trp_ctran: int
    trp_ftra: date
    trp_cdin: int
    trp_ctor: int
    trp_cdor: int
    trp_cpro: int
    trp_qtra: Decimal
    trp_vpro: Decimal
    trp_vcos: Decimal
    trp_iest: str
    trp_tven: int
    trp_desp: str
    trp_tdes: Decimal
    trp_viva: Decimal
    trp_tiva: Decimal
    trp_nlin: int
    trp_ccom: str
    trp_cnit: Decimal
    trp_cmot: int
    trp_lote: int
    trp_vcto: date
    trp_ccos: int
    trp_cfac: int
    trp_horrec: str
    trp_cospro1: Decimal
    trp_cospro2: Decimal
    trp_cospro3: Decimal