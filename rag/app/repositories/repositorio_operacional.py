from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.models.consulta import Consulta
from app.models.respuesta import Respuesta
from app.models.cuestionario import Cuestionario
from app.models.respuesta_cuestionario import RespuestaCuestionario
from app.models.conversacion import Conversacion
from app.models.cuestionario_activo import CuestionarioActivo
from typing import Optional


class RepositorioOperacional:
    """Gestiona operaciones de consultas, cuestionarios, conversaciones y estadísticas."""

    def __init__(self, db: Session):
        self.db = db

    # --- Consultas RAG ---

    def registrar_consulta(self, usuario_id: str, usuario_nombre: str, pregunta: str, conversation_reference: dict = None) -> Consulta:
        consulta = Consulta(
            usuario_id=usuario_id,
            usuario_nombre=usuario_nombre,
            pregunta=pregunta,
            conversation_reference=conversation_reference,
        )
        self.db.add(consulta)
        self.db.commit()
        self.db.refresh(consulta)
        return consulta

    def registrar_respuesta(self, consulta_id: int, respuesta: str, fragmentos: list) -> Respuesta:
        resp = Respuesta(
            consulta_id=consulta_id,
            respuesta=respuesta,
            fragmentos_usados=fragmentos,
        )
        self.db.add(resp)
        self.db.commit()
        return resp

    # --- Cuestionarios ---

    def guardar_cuestionario(self, pregunta: str, respuesta_correcta: str, tema: str) -> Cuestionario:
        cuestionario = Cuestionario(pregunta=pregunta, respuesta_correcta=respuesta_correcta, tema=tema)
        self.db.add(cuestionario)
        self.db.commit()
        self.db.refresh(cuestionario)
        return cuestionario

    def obtener_cuestionario(self, cuestionario_id: int) -> Optional[Cuestionario]:
        return self.db.query(Cuestionario).filter(Cuestionario.id == cuestionario_id).first()

    def obtener_ultimas_preguntas(self, limite: int = 5) -> list[str]:
        rows = (
            self.db.query(Cuestionario.pregunta)
            .order_by(Cuestionario.fecha.desc())
            .limit(limite)
            .all()
        )
        return [r[0] for r in rows]

    def guardar_respuesta_cuestionario(
        self, empleado_id: str, empleado_nombre: str, cuestionario_id: int,
        respuesta: str, score: str, feedback: str
    ) -> RespuestaCuestionario:
        rc = RespuestaCuestionario(
            empleado_id=empleado_id,
            empleado_nombre=empleado_nombre,
            cuestionario_id=cuestionario_id,
            respuesta=respuesta,
            score=score,
            feedback=feedback,
        )
        self.db.add(rc)
        self.db.commit()
        return rc

    # --- Conversaciones ---

    def guardar_conversacion(self, empleado_id: str, empleado_nombre: str, conversation_reference: dict) -> None:
        existente = self.db.query(Conversacion).filter(Conversacion.empleado_id == empleado_id).first()
        if existente:
            existente.empleado_nombre = empleado_nombre
            existente.conversation_reference = conversation_reference
        else:
            self.db.add(Conversacion(
                empleado_id=empleado_id,
                empleado_nombre=empleado_nombre,
                conversation_reference=conversation_reference,
            ))
        self.db.commit()

    def listar_conversaciones(self) -> list[Conversacion]:
        return self.db.query(Conversacion).all()

    # --- Cuestionarios activos ---

    def guardar_cuestionario_activo(self, empleado_id: str, cuestionario_id: int) -> None:
        existente = self.db.query(CuestionarioActivo).filter(CuestionarioActivo.empleado_id == empleado_id).first()
        if existente:
            existente.cuestionario_id = cuestionario_id
        else:
            self.db.add(CuestionarioActivo(empleado_id=empleado_id, cuestionario_id=cuestionario_id))
        self.db.commit()

    def obtener_cuestionario_activo(self, empleado_id: str) -> Optional[CuestionarioActivo]:
        return self.db.query(CuestionarioActivo).filter(CuestionarioActivo.empleado_id == empleado_id).first()

    def eliminar_cuestionario_activo(self, empleado_id: str) -> None:
        self.db.query(CuestionarioActivo).filter(CuestionarioActivo.empleado_id == empleado_id).delete()
        self.db.commit()

    # --- Estadísticas ---

    def usuarios_activos(self) -> list[dict]:
        # Totales por usuario
        totales_subq = (
            self.db.query(
                Consulta.usuario_id,
                func.count(Consulta.id).label("total_consultas"),
                func.max(Consulta.id).label("ultima_id"),
            )
            .filter(Consulta.usuario_id != None, Consulta.usuario_id != "")
            .group_by(Consulta.usuario_id)
            .subquery()
        )
        rows = (
            self.db.query(
                Consulta.usuario_id,
                Consulta.usuario_nombre,
                Consulta.conversation_reference,
                totales_subq.c.total_consultas,
                Consulta.fecha,
            )
            .join(totales_subq, Consulta.id == totales_subq.c.ultima_id)
            .order_by(Consulta.fecha.desc())
            .all()
        )
        return [
            {
                "usuario_id": r[0],
                "usuario_nombre": r[1],
                "conversation_reference": r[2],
                "total_consultas": r[3],
                "ultima_consulta": r[4].isoformat(),
            }
            for r in rows
        ]

    def estadisticas_por_empleado(self) -> list[dict]:
        rows = (
            self.db.query(
                RespuestaCuestionario.empleado_nombre,
                func.count(RespuestaCuestionario.id).label("total"),
                func.sum(case((RespuestaCuestionario.score == "correcto", 1), else_=0)).label("correctas"),
                func.sum(case((RespuestaCuestionario.score == "parcial", 1), else_=0)).label("parciales"),
                func.sum(case((RespuestaCuestionario.score == "incorrecto", 1), else_=0)).label("incorrectas"),
            )
            .group_by(RespuestaCuestionario.empleado_nombre)
            .order_by(func.count(RespuestaCuestionario.id).desc())
            .all()
        )
        return [
            {
                "nombre": r[0],
                "total": r[1],
                "correctas": r[2] or 0,
                "parciales": r[3] or 0,
                "incorrectas": r[4] or 0,
                "porcentaje": round(((r[2] or 0) / r[1]) * 100, 1) if r[1] > 0 else 0,
            }
            for r in rows
        ]

    def ultimas_respuestas(self, limite: int = 20) -> list[dict]:
        rows = (
            self.db.query(
                RespuestaCuestionario.empleado_nombre,
                Cuestionario.pregunta,
                RespuestaCuestionario.respuesta,
                RespuestaCuestionario.score,
                RespuestaCuestionario.feedback,
                RespuestaCuestionario.fecha,
            )
            .join(Cuestionario)
            .order_by(RespuestaCuestionario.fecha.desc())
            .limit(limite)
            .all()
        )
        return [
            {
                "empleado": r[0],
                "pregunta": r[1],
                "respuesta": r[2],
                "score": r[3],
                "feedback": r[4],
                "fecha": r[5].isoformat(),
            }
            for r in rows
        ]
