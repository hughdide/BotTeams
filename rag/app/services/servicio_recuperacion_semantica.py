from app.repositories.repositorio_vectorial import RepositorioVectorial
from app.services.servicio_embeddings import ServicioEmbeddings

# Distancia máxima para considerar un fragmento relevante
UMBRAL_DISTANCIA = 1.5


class ServicioRecuperacionSemantica:
    """Recupera fragmentos documentales relevantes para una consulta."""

    def __init__(self, repo_vectorial: RepositorioVectorial, servicio_embeddings: ServicioEmbeddings):
        self.repo_vec = repo_vectorial
        self.embeddings = servicio_embeddings

    def recuperar(self, pregunta: str, top_k: int = 3) -> list[str]:
        """Devuelve los fragmentos más similares a la pregunta."""
        vector = self.embeddings.generar(pregunta)
        resultados = self.repo_vec.buscar_similares(vector, top_k=top_k)
        return [
            r["texto"] for r in resultados
            if r["distancia"] is None or r["distancia"] < UMBRAL_DISTANCIA
        ]
