from fastapi import FastAPI
from app.api.endpoints import auth, listados
from app.utils.api_helpers import raise_api_error
from app.utils.cache_utils import gettxt
import os
import uvicorn

# Crea la aplicación principal de FastAPI
app = FastAPI(
    title="API de POS - Migración 4GL",
    description="Backend para el sistema POS de restaurante."
)

# Incluye los routers (endpoints) que creamos
app.include_router(auth.router, prefix="/api")
app.include_router(listados.router, prefix="/api")

# --- Endpoints de Prueba ---

@app.get("/")
async def root():
    """Endpoint 'Hello World' para verificar que el servidor corre."""
    return {"message": "¡API del POS funcionando!"}

@app.get("/test-gettxt")
async def test_gettxt():
    """Prueba nuestra función gettxt migrada de C."""
    # (Asegúrate de tener 'textos/stx.tbl' con este contenido)
    # 4GL: LET key = "progerr","|"
    key = "progerr         |" 
    mensaje = gettxt("stx.tbl", key)
    
    if not mensaje:
        return {"error": "No se encontró la clave 'progerr' en 'textos/stx.tbl'"}
        
    return {"clave": key.strip(), "mensaje": mensaje.strip()}

@app.get("/test-error")
async def test_error():
    """Prueba nuestro manejador de errores migrado de fconfir."""
    # 4GL: CALL fconfir("E","PRUEBA DE ERROR")
    raise_api_error("PRUEBA DE ERROR")

# --- Comando para correr el servidor ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)