from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settings

# En app/db/database.py (alrededor de la línea 7)

# Solicitamos la dirección IP del host de Supabase de la URL
host = settings.DATABASE_URL.split('@')[-1].split(':')[0]

# Creamos el motor de la BD
engine = create_engine(
    settings.DATABASE_URL.replace('postgresql://', 'postgresql+psycopg2://'),
    connect_args={'host': host} # Forzamos la conexión por host, no por socket o IPv6
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