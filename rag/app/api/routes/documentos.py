from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.security import verify_api_key
from app.services.servicio_procesamiento_documental import ServicioProcesamientoDocumental
from app.services.servicio_embeddings import ServicioEmbeddings
from app.repositories.repositorio_vectorial import RepositorioVectorial
from app.schemas.documento_schema import DocumentoSubidoResponse, DocumentoListadoResponse

router = APIRouter(prefix="/documentos", tags=["Documentos"])


def _servicio(db: Session) -> ServicioProcesamientoDocumental:
    """Construye el servicio con sus dependencias."""
    repo_vec = RepositorioVectorial()
    embeddings = ServicioEmbeddings()
    return ServicioProcesamientoDocumental(db, repo_vec, embeddings)


@router.post("", response_model=DocumentoSubidoResponse)
async def subir_documento(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    """Sube, fragmenta e indexa un documento."""
    servicio = _servicio(db)
    return servicio.procesar_documento(file)


@router.get("", response_model=list[DocumentoListadoResponse])
def listar_documentos(
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    """Devuelve todos los documentos registrados."""
    servicio = _servicio(db)
    return servicio.listar_documentos()


@router.get("/{nombre}")
def descargar_documento(
    nombre: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    """Descarga el archivo original por nombre."""
    servicio = _servicio(db)
    ruta = servicio.obtener_ruta(nombre)
    if not ruta:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return FileResponse(ruta, filename=nombre)
