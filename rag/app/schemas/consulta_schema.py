from pydantic import BaseModel
from typing import Optional


class ConsultaRequest(BaseModel):
    pregunta: str
    usuario_id: Optional[str] = None
    usuario_nombre: Optional[str] = None
    conversation_reference: Optional[dict] = None


class ConsultaResponse(BaseModel):
    respuesta: str
    consulta_id: Optional[int] = None
    fragmentos_encontrados: int = 0
