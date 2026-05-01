from pydantic import BaseModel
from typing import List, Optional


class Experiencia(BaseModel):
    cargo: str
    empresa: str
    periodo: Optional[str] = ""
    atividades: List[str]


class Curriculo(BaseModel):
    nome: str
    data_nascimento: Optional[str] = ""
    estado_civil: Optional[str] = ""
    cnh: Optional[str] = ""
    telefone: Optional[str] = ""
    email: Optional[str] = ""
    resumo: str
    experiencias: List[Experiencia]
    formacao: List[str]
    cursos: List[str]
    habilidades: List[str]
