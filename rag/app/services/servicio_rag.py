import anthropic
from sqlalchemy.orm import Session
from app.services.servicio_recuperacion_semantica import ServicioRecuperacionSemantica
from app.repositories.repositorio_operacional import RepositorioOperacional
from app.core.config import settings

PROMPT_SISTEMA = (
    "Eres el asistente interno de la empresa. "
    "Responde ÚNICAMENTE basándote en el contexto proporcionado. "
    "Si la pregunta no tiene relación con el contexto, responde exactamente: "
    "'No tengo información sobre ese tema en los documentos de la empresa.' "
    "Responde siempre en español."
)


class ServicioRAG:
    """Ejecuta el flujo completo de Retrieval-Augmented Generation."""

    def __init__(self, db: Session, servicio_recuperacion: ServicioRecuperacionSemantica):
        self.repo_op = RepositorioOperacional(db)
        self.recuperacion = servicio_recuperacion
        self.llm = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def consultar(self, pregunta: str, usuario_id: str = "", usuario_nombre: str = "", conversation_reference: dict = None) -> dict:
        """Recupera contexto, llama al LLM y persiste la consulta y respuesta."""
        consulta = self.repo_op.registrar_consulta(usuario_id, usuario_nombre, pregunta, conversation_reference)
        fragmentos = self.recuperacion.recuperar(pregunta)

        if not fragmentos:
            respuesta_texto = "No encontré información relevante en los documentos de la empresa."
            self.repo_op.registrar_respuesta(consulta.id, respuesta_texto, [])
            return {"respuesta": respuesta_texto, "consulta_id": consulta.id, "fragmentos_encontrados": 0}

        contexto = "\n\n".join(fragmentos)
        prompt = f"Contexto:\n{contexto}\n\nPregunta: {pregunta}"

        mensaje = self.llm.messages.create(
            model=settings.llm_model,
            max_tokens=1024,
            system=PROMPT_SISTEMA,
            messages=[{"role": "user", "content": prompt}],
        )
        respuesta_texto = mensaje.content[0].text
        self.repo_op.registrar_respuesta(consulta.id, respuesta_texto, fragmentos)

        return {
            "respuesta": respuesta_texto,
            "consulta_id": consulta.id,
            "fragmentos_encontrados": len(fragmentos),
        }
