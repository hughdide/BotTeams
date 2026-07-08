from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.security import verify_api_key
from app.services.servicio_conversaciones import ServicioConversaciones
from app.schemas.cuestionario_schema import ConversacionRequest, CuestionarioActivoRequest

router = APIRouter(prefix="/conversaciones", tags=["Conversaciones"])


@router.post("")
def guardar_conversacion(
    body: ConversacionRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    """Guarda o actualiza la referencia de conversación de un empleado."""
    ServicioConversaciones(db).guardar(body.empleado_id, body.empleado_nombre, body.conversation_reference)
    return {"status": "ok"}


@router.get("")
def listar_conversaciones(
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    """Lista todas las referencias de conversación almacenadas."""
    return ServicioConversaciones(db).listar()


@router.post("/cuestionarios-activos")
def guardar_cuestionario_activo(
    body: CuestionarioActivoRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    """Registra el cuestionario pendiente de respuesta para un empleado."""
    ServicioConversaciones(db).guardar_cuestionario_activo(body.empleado_id, body.cuestionario_id)
    return {"status": "ok"}


@router.get("/cuestionarios-activos/{empleado_id}")
def obtener_cuestionario_activo(
    empleado_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    """Obtiene el cuestionario activo de un empleado."""
    cuestionario_id = ServicioConversaciones(db).obtener_cuestionario_activo(empleado_id)
    if cuestionario_id is None:
        raise HTTPException(status_code=404, detail="No hay cuestionario activo")
    return {"cuestionario_id": cuestionario_id}


@router.delete("/cuestionarios-activos/{empleado_id}")
def eliminar_cuestionario_activo(
    empleado_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    """Elimina el cuestionario activo de un empleado tras ser evaluado."""
    ServicioConversaciones(db).eliminar_cuestionario_activo(empleado_id)
    return {"status": "ok"}
