from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.security import verify_api_key
from app.services.servicio_evaluacion import ServicioEvaluacion
from app.schemas.evaluacion_schema import EvaluarRespuestaRequest, EvaluacionResponse

router = APIRouter(prefix="/evaluaciones", tags=["Evaluaciones"])


@router.post("", response_model=EvaluacionResponse)
def evaluar_respuesta(
    body: EvaluarRespuestaRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    """Evalúa la respuesta de un empleado y guarda el resultado."""
    try:
        servicio = ServicioEvaluacion(db)
        return servicio.evaluar(
            cuestionario_id=body.cuestionario_id,
            empleado_id=body.empleado_id,
            empleado_nombre=body.empleado_nombre,
            respuesta=body.respuesta,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
