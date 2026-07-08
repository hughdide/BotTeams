from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DocumentoSubidoResponse(BaseModel):
    id: int
    nombre: str
    estado: str
    fragmentos_creados: int


class DocumentoListadoResponse(BaseModel):
    id: int
    nombre: str
    tipo_mime: Optional[str]
    tamano_bytes: Optional[int]
    estado: str
    fecha_subida: datetime

    class Config:
        from_attributes = True
