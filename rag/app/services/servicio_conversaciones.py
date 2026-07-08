from sqlalchemy.orm import Session
from app.repositories.repositorio_operacional import RepositorioOperacional


class ServicioConversaciones:
    """Gestiona referencias de conversación y cuestionarios activos por empleado."""

    def __init__(self, db: Session):
        self.repo_op = RepositorioOperacional(db)

    def guardar(self, empleado_id: str, empleado_nombre: str, conversation_reference: dict) -> None:
        """Guarda o actualiza la referencia de conversación (upsert)."""
        self.repo_op.guardar_conversacion(empleado_id, empleado_nombre, conversation_reference)

    def listar(self) -> list[dict]:
        """Devuelve todas las conversaciones almacenadas."""
        return [
            {
                "empleado_id": c.empleado_id,
                "empleado_nombre": c.empleado_nombre,
                "conversation_reference": c.conversation_reference,
            }
            for c in self.repo_op.listar_conversaciones()
        ]

    def guardar_cuestionario_activo(self, empleado_id: str, cuestionario_id: int) -> None:
        """Registra el cuestionario pendiente de respuesta para un empleado."""
        self.repo_op.guardar_cuestionario_activo(empleado_id, cuestionario_id)

    def obtener_cuestionario_activo(self, empleado_id: str) -> int | None:
        """Devuelve el cuestionario_id activo del empleado, o None si no tiene."""
        activo = self.repo_op.obtener_cuestionario_activo(empleado_id)
        return activo.cuestionario_id if activo else None

    def eliminar_cuestionario_activo(self, empleado_id: str) -> None:
        """Elimina el cuestionario activo tras ser evaluado."""
        self.repo_op.eliminar_cuestionario_activo(empleado_id)
