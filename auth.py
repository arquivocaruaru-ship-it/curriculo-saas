from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
import os
from typing import Optional

# =========================
# CONFIGURAÇÃO
# =========================

# Configuração do hashing de senha
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "bcrypt"],  # bcrypt como fallback
    deprecated="auto",
    pbkdf2_sha256__default_rounds=29000,  # rounds para maior segurança
)

# Configuração do JWT (para futuro sistema de token)
SECRET_KEY = os.getenv("SECRET_KEY", "sua-chave-secreta-aqui-mude-em-producao")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# =========================
# FUNÇÕES DE HASH DE SENHA
# =========================

def hash_senha(senha: str) -> str:
    """
    Gera hash da senha usando pbkdf2_sha256
    
    Args:
        senha: Senha em texto plano
        
    Returns:
        Hash da senha
    """
    if not senha:
        raise ValueError("Senha não pode ser vazia")
    
    return pwd_context.hash(senha)


def verificar_senha(senha: str, hash_senha: str) -> bool:
    """
    Verifica se a senha corresponde ao hash
    
    Args:
        senha: Senha em texto plano
        hash_senha: Hash armazenado no banco
        
    Returns:
        True se a senha é válida, False caso contrário
    """
    if not senha or not hash_senha:
        return False
    
    try:
        return pwd_context.verify(senha, hash_senha)
    except Exception:
        return False


def validar_forca_senha(senha: str) -> tuple[bool, str]:
    """
    Valida a força da senha
    
    Args:
        senha: Senha a ser validada
        
    Returns:
        (é_valida, mensagem)
    """
    if len(senha) < 6:
        return False, "Senha deve ter pelo menos 6 caracteres"
    
    if len(senha) > 72:
        return False, "Senha muito longa (máximo 72 caracteres)"
    
    # Verifica se tem pelo menos um número
    if not any(char.isdigit() for char in senha):
        return False, "Senha deve conter pelo menos um número"
    
    # Verifica se tem pelo menos uma letra
    if not any(char.isalpha() for char in senha):
        return False, "Senha deve conter pelo menos uma letra"
    
    return True, "Senha válida"


# =========================
# FUNÇÕES JWT (TOKEN)
# =========================

def criar_token_acesso(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um token JWT para autenticação
    
    Args:
        data: Dados a serem codificados no token
        expires_delta: Tempo de expiração (opcional)
        
    Returns:
        Token JWT
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verificar_token_acesso(token: str) -> Optional[dict]:
    """
    Verifica e decodifica um token JWT
    
    Args:
        token: Token JWT a ser verificado
        
    Returns:
        Dados decodificados ou None se inválido
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        print("Token expirado")
        return None
    except jwt.InvalidTokenError as e:
        print(f"Token inválido: {e}")
        return None


# =========================
# FUNÇÕES AUXILIARES
# =========================

def gerar_senha_temporaria() -> str:
    """
    Gera uma senha temporária para recuperação de conta
    
    Returns:
        Senha temporária de 8 caracteres
    """
    import random
    import string
    
    caracteres = string.ascii_letters + string.digits
    senha = ''.join(random.choices(caracteres, k=8))
    
    return senha


def mascarar_email(email: str) -> str:
    """
    Mascara o email para exibição parcial
    
    Exemplo: joa***@gmail.com
    
    Args:
        email: Email original
        
    Returns:
        Email mascarado
    """
    if '@' not in email:
        return email
    
    local, domain = email.split('@', 1)
    
    if len(local) <= 3:
        mascara = '*' * len(local)
    else:
        mascara = local[:3] + '*' * (len(local) - 3)
    
    return f"{mascara}@{domain}"


# =========================
# EXEMPLO DE USO (COMENTADO)
# =========================

# if __name__ == "__main__":
#     # Teste de hash
#     senha = "minhaSenha123"
#     hash_valor = hash_senha(senha)
#     print(f"Hash: {hash_valor}")
#     
#     # Teste de verificação
#     valido = verificar_senha(senha, hash_valor)
#     print(f"Senha válida: {valido}")
#     
#     # Teste de força da senha
#     valido, msg = validar_forca_senha(senha)
#     print(f"Força da senha: {msg}")
#     
#     # Teste de token JWT
#     token = criar_token_acesso({"user_id": 1, "email": "teste@email.com"})
#     print(f"Token: {token}")
#     
#     # Teste de verificação de token
#     payload = verificar_token_acesso(token)
#     print(f"Payload: {payload}")