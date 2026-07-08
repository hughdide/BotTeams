from pydantic import BaseModel
from typing import Optional


class GenerarCuestionarioRequest(BaseModel):
    tema: Optional[str] = None


class CuestionarioGeneradoResponse(BaseModel):
    cuestionario_id: int
    pregunta: str


class ConversacionRequest(BaseModel):
    empleado_id: str
    empleado_nombre: str
    conversation_reference: dict


class CuestionarioActivoRequest(BaseModel):
    empleado_id: str
    cuestionario_id: int
