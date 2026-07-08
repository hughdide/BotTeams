from pydantic import BaseModel


class EvaluarRespuestaRequest(BaseModel):
    cuestionario_id: int
    empleado_id: str
    empleado_nombre: str
    respuesta: str


class EvaluacionResponse(BaseModel):
    score: str
    feedback: str
    respuesta_correcta: str
