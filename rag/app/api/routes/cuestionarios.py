from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.security import verify_api_key
from app.services.servicio_cuestionarios import ServicioCuestionarios
from app.services.servicio_recuperacion_semantica import ServicioRecuperacionSemantica
from app.services.servicio_embeddings import ServicioEmbeddings
from app.repositories.repositorio_vectorial import RepositorioVectorial
from app.schemas.cuestionario_schema import GenerarCuestionarioRequest, CuestionarioGeneradoResponse

router = APIRouter(prefix="/cuestionarios", tags=["Cuestionarios"])


def _servicio(db: Session) -> ServicioCuestionarios:
    """Construye el servicio de cuestionarios con sus dependencias."""
    repo_vec = RepositorioVectorial()
    embeddings = ServicioEmbeddings()
    recuperacion = ServicioRecuperacionSemantica(repo_vec, embeddings)
    return ServicioCuestionarios(db, recuperacion)


@router.post("/generar", response_model=CuestionarioGeneradoResponse)
def generar_cuestionario(
    body: GenerarCuestionarioRequest = GenerarCuestionarioRequest(),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    """Genera una pregunta de cuestionario sobre el contenido indexado."""
    try:
        servicio = _servicio(db)
        return servicio.generar(tema=body.tema)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
