from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.security import verify_api_key
from app.services.servicio_rag import ServicioRAG
from app.services.servicio_recuperacion_semantica import ServicioRecuperacionSemantica
from app.services.servicio_embeddings import ServicioEmbeddings
from app.repositories.repositorio_vectorial import RepositorioVectorial
from app.schemas.consulta_schema import ConsultaRequest, ConsultaResponse

router = APIRouter(prefix="/consultas", tags=["Consultas"])


def _servicio(db: Session) -> ServicioRAG:
    """Construye el servicio RAG con sus dependencias."""
    repo_vec = RepositorioVectorial()
    embeddings = ServicioEmbeddings()
    recuperacion = ServicioRecuperacionSemantica(repo_vec, embeddings)
    return ServicioRAG(db, recuperacion)


@router.post("", response_model=ConsultaResponse)
def realizar_consulta(
    body: ConsultaRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    """Ejecuta el flujo RAG y devuelve la respuesta generada."""
    servicio = _servicio(db)
    return servicio.consultar(
        pregunta=body.pregunta,
        usuario_id=body.usuario_id or "",
        usuario_nombre=body.usuario_nombre or "",
        conversation_reference=body.conversation_reference,
    )
