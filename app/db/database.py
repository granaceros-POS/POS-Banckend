from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settings

# Importaciones y configuración para forzar la lectura correcta de DECIMAL
import psycopg2.extensions
import decimal
import sys
import os

# --- CONFIGURACIÓN DE TIPIFICACIÓN (EL FIX CRÍTICO) ---
# Esto le dice a psycopg2 que si ve un tipo NUMERIC/DECIMAL (código 1700),
# lo convierta directamente al tipo Decimal de Python.
DECIMAL_OID = 1700
def cast_decimal(value, cursor):
    if value is None:
        return None
    return decimal.Decimal(value)

# Solo registramos el tipo si la base de datos está conectada.
try:
    psycopg2.extensions.register_type(psycopg2.extensions.new_type((DECIMAL_OID,), 'DECIMAL', cast_decimal))
except Exception:
    # Ignoramos si la importación falla al inicio (como en algunos entornos de prueba)
    pass 
# -------------------------------------------------------

# 1. Solicitamos el host de Supabase de la URL
try:
    host = settings.DATABASE_URL.split('@')[-1].split(':')[0]
except IndexError:
    host = None

# 2. Creamos el motor de la BD
engine = create_engine(
    # Usamos el dialecto explícito para evitar el problema de socket/red
    settings.DATABASE_URL.replace('postgresql://', 'postgresql+psycopg2://'),
    connect_args={'host': host} if host else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    Función de utilidad para abrir y cerrar la conexión 
    a la base de datos en cada solicitud de API.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()