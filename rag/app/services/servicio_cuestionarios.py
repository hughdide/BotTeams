import json
import re
import random
import anthropic
from sqlalchemy.orm import Session
from app.services.servicio_recuperacion_semantica import ServicioRecuperacionSemantica
from app.repositories.repositorio_operacional import RepositorioOperacional
from app.core.config import settings

TEMAS_DEFAULT = ["procedimientos", "políticas", "normas", "empresa", "empleados"]


class ServicioCuestionarios:
    """Genera preguntas de cuestionario a partir del contenido indexado."""

    def __init__(self, db: Session, servicio_recuperacion: ServicioRecuperacionSemantica):
        self.repo_op = RepositorioOperacional(db)
        self.recuperacion = servicio_recuperacion
        self.llm = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def generar(self, tema: str | None = None) -> dict:
        """Genera una pregunta única evitando repetir las últimas 5."""
        tema = tema or random.choice(TEMAS_DEFAULT)
        fragmentos = self.recuperacion.recuperar(tema, top_k=5)

        if not fragmentos:
            raise ValueError("No hay documentos indexados para generar cuestionarios.")

        ultimas = self.repo_op.obtener_ultimas_preguntas(5)
        ultimas_str = "\n".join(ultimas) if ultimas else "Ninguna"
        contexto = "\n".join(fragmentos)

        prompt = f"""Basándote en este contenido de la empresa:
{contexto}

Preguntas ya realizadas (NO repitas):
{ultimas_str}

Genera UNA pregunta sobre el tema: "{tema}"
Responde ÚNICAMENTE con este JSON sin texto adicional:
{{"pregunta": "la pregunta aquí", "respuesta_correcta": "la respuesta correcta aquí"}}"""

        mensaje = self.llm.messages.create(
            model=settings.llm_model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        texto = mensaje.content[0].text.strip()

        match = re.search(r'\{.*?\}', texto, re.DOTALL)
        if not match:
            raise ValueError("No se pudo parsear la respuesta del LLM.")

        data = json.loads(match.group())
        cuestionario = self.repo_op.guardar_cuestionario(
            pregunta=data["pregunta"],
            respuesta_correcta=data["respuesta_correcta"],
            tema=tema,
        )

        return {"cuestionario_id": cuestionario.id, "pregunta": cuestionario.pregunta}
