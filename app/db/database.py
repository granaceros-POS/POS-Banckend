from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settings

# Lee la DATABASE_URL de tu .env
engine = create_engine(settings.DATABASE_URL)

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