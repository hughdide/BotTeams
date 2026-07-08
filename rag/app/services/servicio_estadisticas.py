from sqlalchemy.orm import Session
from app.repositories.repositorio_operacional import RepositorioOperacional


class ServicioEstadisticas:
    """Proporciona métricas de uso y rendimiento de los empleados."""

    def __init__(self, db: Session):
        self.repo_op = RepositorioOperacional(db)

    def usuarios_activos(self) -> list[dict]:
        """Lista usuarios únicos con su conversation_reference más reciente."""
        return self.repo_op.usuarios_activos()

    def obtener(self) -> dict:
        """Devuelve estadísticas por empleado y las últimas 20 respuestas."""
        return {
            "empleados": self.repo_op.estadisticas_por_empleado(),
            "ultimas_respuestas": self.repo_op.ultimas_respuestas(),
        }
