from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from app.utils.api_helpers import raise_api_error
from fastapi import status
from typing import Literal, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP, getcontext

from app.models.pos_models import InvProResult 

# Configuración de precisión decimal alta
getcontext().prec = 28 


# --- Constantes que simulan la configuración global de costos (grconcos) ---
class CostosConfig:
    COP_TCOS_TIPO_S = "S" 
    COP_ICOC_USA_ESTIMADO = "S" 
    COP_CANN_AJUSTE_NEGATIVO = "S" 

def get_costos_config():
    """Simula la carga de configuración de costos (grconcos)."""
    return CostosConfig()

def round_decimal(value: Decimal, precision: int = 2) -> Decimal:
    """Redondeo para manejar precisión financiera (simulando ROUND1)."""
    return value.quantize(Decimal(f'0.{"0" * precision}'), rounding=ROUND_HALF_UP)


async def finvpro_service(
    lxcpro: int,
    lxcannue: Decimal,
    lxmodulo: int,       # -1 para Salida (Venta/Consumo), 1 para Entrada (Compra/Ajuste)
    rgp_calm: int,       # Código de almacén (grgenera.rgp_calm)
    db: Session,
    lxpar: Literal['A', 'E'] = 'A', # A=Adicionando, E=Eliminando
    licalcos: Literal['S', 'N'] = 'S' # S=Sí calcula/actualiza costo promedio
) -> InvProResult:
    """
    Migración de FUNCTION finvpro().
    Actualiza la cantidad de inventario y recalcula el costo promedio.
    (SIN TRANSACCIÓN PROPIA, confiando en la transacción externa de fdesglos.)
    """
    
    config = get_costos_config()
    
    try:
        # 1. Bloqueo y obtención de datos de inventario (SELECT ... FOR UPDATE)
        inv_query = text("""
            SELECT ppp_qinv, ppp_vcos, ppp_tippro
            FROM ppp_propvt
            WHERE ppp_calm = :rgp_calm AND ppp_cpro = :lxcpro
            FOR UPDATE
        """)
        inv_result = db.execute(inv_query, {'rgp_calm': rgp_calm, 'lxcpro': lxcpro}).fetchone()
        
        # 2. Inicialización y conversión de Decimal (LECTURA SEGURA DE LA BD)
        if inv_result is None:
            lxcanact = Decimal('0.00')
            lxcosact = Decimal('0.00')
            lxtippro = 1 
        else:
            # Conversion segura: Forzamos str() para que Python lo lea correctamente
            lxcanact = Decimal(str(inv_result.ppp_qinv)) if inv_result.ppp_qinv is not None else Decimal('0.00')
            lxcosact = Decimal(str(inv_result.ppp_vcos)) if inv_result.ppp_vcos is not None else Decimal('0.00')
            lxtippro = inv_result.ppp_tippro
            
        
        # 3. Obtener Costo Estimado (cop_costos)
        costo_est_query = text("""
            SELECT cop_vcos
            FROM cop_costos
            WHERE cop_calm = :rgp_calm AND cop_cpro = :lxcpro
        """)
        costo_est_result = db.execute(costo_est_query, {'rgp_calm': rgp_calm, 'lxcpro': lxcpro}).scalar_one_or_none()
        lxcosest = Decimal(str(costo_est_result)) if costo_est_result is not None else Decimal('0.00')

        # 4. Aplicar Reglas de Costos (Grconcos)
        lxcosnue = lxcosact 
        lxcosnue_input = Decimal('0.00') 

        if config.COP_TCOS_TIPO_S == "S":
            lxcosnue = lxcosest
        elif config.COP_ICOC_USA_ESTIMADO == "S" and lxcanact == Decimal('0.00'):
            lxcosnue = lxcosest

        # 5. Cálculo del Nuevo Costo Promedio (solo si licalcos = 'S')
        if licalcos == 'S':
            if lxpar == 'A': 
                nueva_cantidad_total = lxcanact + (lxcannue * lxmodulo)
                if nueva_cantidad_total > Decimal('0.00'):
                    lxcosnue = ((lxcosact * lxcanact) + (lxcosnue_input * lxcannue)) / (lxcanact + lxcannue)
                else:
                    lxcosnue = lxcosact


        # 6. Validación final y Redondeo (ROUND1)
        if lxcosnue is None or lxcosnue < 0:
            lxcosnue = Decimal('0.00')
        
        lxcosnue = round_decimal(lxcosnue)
        
        # 7. Actualización de la BD (UPDATE ppp_propvt)
        update_query = text("""
            UPDATE ppp_propvt
            SET ppp_qinv = ppp_qinv + :cantidad_modificada,
                ppp_vcos = :lxcosnue
            WHERE ppp_calm = :rgp_calm AND ppp_cpro = :lxcpro
        """)
        
        cantidad_modificada = lxcannue * lxmodulo 
        
        db.execute(update_query, {
            'cantidad_modificada': cantidad_modificada,
            'lxcosnue': lxcosnue,
            'rgp_calm': rgp_calm,
            'lxcpro': lxcpro
        })
        
        # OJO: SIN db.commit() AQUÍ. Lo hace la función superior
        
        # Devolver el resultado
        return InvProResult(lxcosnue=lxcosnue, lxtippro=lxtippro)

    except Exception as e:
        # En caso de error, relanzamos la excepción para que fdesglos_service haga el ROLLBACK
        print(f"Error interno en finvpro para producto {lxcpro}: {e}")
        raise e 


async def fdesglos_recursive(
    db: Session,
    lxcpro: int,
    licantid: Decimal,
    lxtven: int,
    lxincsum: Literal['S', 'N'],
    rgp_calm: int,
    # Variables de salida para costos (lxcospro1, 2, 3)
    costo_totales: Optional[Tuple[Decimal, Decimal, Decimal]] = None 
) -> Tuple[Decimal, Decimal, Decimal]:
    """
    Migración de FUNCTION fdesglos() - Lógica recursiva de desglose de recetas.
    """

    if costo_totales is None:
        costo_totales = (Decimal('0.00'), Decimal('0.00'), Decimal('0.00'))
    
    lxcospro1, lxcospro2, lxcospro3 = costo_totales

    # 1. Obtener Componentes de la Receta
    query_componentes = text("""
        SELECT fop_cfor, fop_qfor, fop_icom, T2.inp_itpr
        FROM fop_compro AS T1
        JOIN inp_produc AS T2 ON T1.fop_cfor = T2.inp_cpro
        WHERE T1.fop_cpro = :lxcpro AND T1.fop_tven = :lxtven
    """)
    componentes_result = db.execute(query_componentes, {'lxcpro': lxcpro, 'lxtven': lxtven}).fetchall()
    
    if not componentes_result:
        return costo_totales

    # 2. Iterar sobre los Componentes
    for row in componentes_result:
        comp_cpro = row.fop_cfor
        comp_qfor = Decimal(str(row.fop_qfor))
        comp_icom = row.fop_icom
        comp_itpr = row.inp_itpr 
        
        # Cantidad a mover (siempre debe ser Decimal)
        cantidad_a_mover = licantid * comp_qfor
        
        if comp_icom == 'S' and lxincsum == 'N':
            continue 

        # Condición de Recursión (Receta dentro de Receta)
        if comp_itpr == 21:
            costos_recursivos = await fdesglos_recursive(
                db=db,
                lxcpro=comp_cpro,
                licantid=cantidad_a_mover, 
                lxtven=lxtven,
                lxincsum=lxincsum,
                rgp_calm=rgp_calm,
                costo_totales=costo_totales 
            )
            lxcospro1 += costos_recursivos[0]
            lxcospro2 += costos_recursivos[1]
            lxcospro3 += costos_recursivos[2]
            
        else:
            # Lógica de Actualización de Inventario (finvpro)
            finvpro_result = await finvpro_service(
                lxcpro=comp_cpro,
                lxcannue=cantidad_a_mover,
                lxmodulo=-1, 
                rgp_calm=rgp_calm,
                db=db,
                lxpar='E', 
                licalcos='N'
            )
            
            # 4. Acumulación de Costos (¡El arreglo del costo cero!)
            # FORZAMOS LA CONVERSIÓN A DECIMAL ANTES DE LA SUMA
            lxcospro = finvpro_result.lxcosnue * cantidad_a_mover
            
            # Acumulación por Tipo de Producto (lxtippro)
            match finvpro_result.lxtippro:
                case 1: # Materia Prima (lxcospro1)
                    lxcospro1 += lxcospro
                case 2: # Suministro (lxcospro2)
                    lxcospro2 += lxcospro
                case 3: # Mano de Obra (lxcospro3)
                    lxcospro3 += lxcospro
    
    # 5. Devolver Costos Totales de esta rama
    return (lxcospro1, lxcospro2, lxcospro3)


async def fdesglos_service(
    db: Session,
    lxcpro: int,
    licantid: Decimal,
    lxtven: int,
    rgp_calm: int,
    lxincsum: Literal['S', 'N'] = 'S' # Incluye Suministros (S/N)
) -> Tuple[Decimal, Decimal, Decimal]:
    """
    Función de entrada para el desglose de recetas (simula la llamada inicial a fdesglos).
    CONTIENE LA TRANSACCIÓN ÚNICA (db.begin() / db.commit()).
    """
    
    try:
        # INICIO DE LA TRANSACCIÓN ÚNICA (BEGIN WORK)
        db.begin()
        
        # Llamamos a la función recursiva
        costos = await fdesglos_recursive(
            db=db,
            lxcpro=lxcpro,
            licantid=licantid,
            lxtven=lxtven,
            lxincsum=lxincsum,
            rgp_calm=rgp_calm
        )

        # COMMIT DE LA TRANSACCIÓN (COMMIT WORK) si todo es exitoso
        db.commit()
        return costos
        
    except Exception as e:
        # ROLLBACK si algo falla en la recursión o el finvpro anidado
        db.rollback()
        # Esto lanzará el error 500 que vemos en el navegador
        raise e