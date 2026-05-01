from sqlalchemy import Column, Integer, String, ForeignKey, Text
from database import Base

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    senha = Column(String)

class Curriculo(Base):
    __tablename__ = "curriculos"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("usuarios.id"))
    dados_brutos = Column(Text)
    dados_tratados = Column(Text, nullable=True)
    foto = Column(String, nullable=True)
    modelo = Column(Integer, default=1)