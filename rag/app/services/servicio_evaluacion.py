import json
import re
import anthropic
from sqlalchemy.orm import Session
from app.repositories.repositorio_operacional import RepositorioOperacional
from app.core.config import settings


class ServicioEvaluacion:
    """Evalúa la respuesta de un empleado a una pregunta de cuestionario."""

    def __init__(self, db: Session):
        self.repo_op = RepositorioOperacional(db)
        self.llm = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def evaluar(self, cuestionario_id: int, empleado_id: str, empleado_nombre: str, respuesta: str) -> dict:
        """Pide al LLM que evalúe la respuesta y persiste el resultado."""
        cuestionario = self.repo_op.obtener_cuestionario(cuestionario_id)
        if not cuestionario:
            raise ValueError(f"Cuestionario {cuestionario_id} no encontrado.")

        prompt = f"""Evalúa esta respuesta de un empleado:
Pregunta: {cuestionario.pregunta}
Respuesta correcta: {cuestionario.respuesta_correcta}
Respuesta del empleado: {respuesta}

Responde ÚNICAMENTE con este JSON sin texto adicional:
{{"score": "correcto|parcial|incorrecto", "feedback": "explicación breve en español"}}"""

        mensaje = self.llm.messages.create(
            model=settings.llm_model,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        texto = mensaje.content[0].text.strip()

        match = re.search(r'\{.*?\}', texto, re.DOTALL)
        if not match:
            raise ValueError("No se pudo parsear la evaluación del LLM.")

        data = json.loads(match.group())
        self.repo_op.guardar_respuesta_cuestionario(
            empleado_id=empleado_id,
            empleado_nombre=empleado_nombre,
            cuestionario_id=cuestionario_id,
            respuesta=respuesta,
            score=data["score"],
            feedback=data["feedback"],
        )

        return {
            "score": data["score"],
            "feedback": data["feedback"],
            "respuesta_correcta": cuestionario.respuesta_correcta,
        }
