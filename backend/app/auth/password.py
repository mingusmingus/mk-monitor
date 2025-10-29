"""
Gestión de contraseñas:

- hash_password(plain): genera hash seguro con bcrypt.
- verify_password(plain, hashed): compara contraseña.
"""
import bcrypt

def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))