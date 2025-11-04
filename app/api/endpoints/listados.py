from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.sql import text # Para ejecutar SQL de forma segura
from app.db.database import get_db
from app.utils.common_utils import handle_api_errors
from app.utils.api_helpers import raise_api_error
import math

router = APIRouter()

# Modelo de respuesta: Qué le devolveremos a la app de Android
class PaginatedListResponse(BaseModel):
    total_rows: int
    total_pages: int
    current_page: int
    items: list[dict] # Los datos irán aquí

@router.get("/listado/{list_name}", response_model=PaginatedListResponse, tags=["Listados"])
@handle_api_errors
async def get_listado(
    list_name: str,
    page: int = 1,
    limit: int = 20,
    search: str | None = None,
    db: Session = Depends(get_db)
):
    """
    Endpoint genérico que reemplaza list.4gl
    """

    # --- Lógica de 'listsetup' ---
    # Aquí definimos las consultas SQL para cada lista
    if list_name == "productos":
        tables = "ppp_propvt"
        items = "ppp_cpro, ppp_dpro" # (Asumimos que ppp_dpro es la descripción)
        search_field = "ppp_dpro"
        order = "ppp_cpro"
        base_filter = "ppp_calm = 1" # (Ej: grgenera.rgp_calm)

    # (Puedes añadir más listas aquí)
    # elif list_name == "clientes":
    #     tables = "clp_client"
    #     items = "clp_ncli, clp_dnom"
    #     search_field = "clp_dnom"
    #     order = "clp_dnom"
    #     base_filter = "1=1"

    else:
        # Si la lista no está definida, devolvemos un error
        raise_api_error(f"El listado '{list_name}' no está definido.", status.HTTP_404_NOT_FOUND)

    # --- Lógica de 'listman' (Búsqueda y Paginación) ---

    # 1. CONSTRUIR FILTRO
    sql_filter = base_filter
    params = {} # Parámetros seguros

    if search:
        # Usamos ILIKE para búsquedas 'case-insensitive' en PostgreSQL
        sql_filter += f" AND {search_field} ILIKE :search"
        params["search"] = f"%{search}%"

    # 2. CONSULTA DE CONTEO
    count_query = text(f"SELECT COUNT(*) FROM {tables} WHERE {sql_filter}")
    total_rows = db.execute(count_query, params).scalar_one()
    total_pages = math.ceil(total_rows / limit)

    # 3. CONSULTA DE DATOS (Paginada)
    offset = (page - 1) * limit
    data_query = text(f"""
        SELECT {items} 
        FROM {tables} 
        WHERE {sql_filter} 
        ORDER BY {order}
        LIMIT :limit OFFSET :offset
    """)

    params["limit"] = limit
    params["offset"] = offset

    result_proxy = db.execute(data_query, params)

    # Convertir resultados a JSON (lista de diccionarios)
    items_list = [dict(row._mapping) for row in result_proxy]

    return {
        "total_rows": total_rows,
        "total_pages": total_pages,
        "current_page": page,
        "items": items_list
    }