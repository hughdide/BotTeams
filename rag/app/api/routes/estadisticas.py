from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.security import verify_api_key
from app.services.servicio_estadisticas import ServicioEstadisticas

router = APIRouter(prefix="/estadisticas", tags=["Estadísticas"])


@router.get("")
def obtener_estadisticas(
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    """Devuelve métricas por empleado y últimas 20 respuestas."""
    return ServicioEstadisticas(db).obtener()


@router.get("/usuarios")
def listar_usuarios_activos(
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    """Lista los usuarios únicos que han realizado consultas, con su conversation_reference."""
    return ServicioEstadisticas(db).usuarios_activos()
