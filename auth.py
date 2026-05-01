from passlib.context import CryptContext
import random
import string

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def hash_senha(senha: str):
    return pwd_context.hash(senha)

def verificar_senha(senha: str, hash: str):
    return pwd_context.verify(senha, hash)

def validar_forca_senha(senha: str):
    if len(senha) < 6:
        return False, "Senha deve ter pelo menos 6 caracteres"
    if len(senha) > 72:
        return False, "Senha muito longa (máximo 72 caracteres)"
    return True, "Senha válida"

def gerar_senha_temporaria():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))