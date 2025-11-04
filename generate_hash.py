from passlib.context import CryptContext

print("Generando nuevo hash para 'clave123'...")

# Definimos el contexto, igual que en security.py
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

# Creamos el hash
nuevo_hash = pwd_context.hash("clave123", scheme="argon2")

print("\n¡LISTO!")
print("--- COPIA LA LÍNEA DE ABAJO COMPLETA (empieza con $argon2id$) ---")
print(nuevo_hash)
print("-----------------------------------------------------------------")