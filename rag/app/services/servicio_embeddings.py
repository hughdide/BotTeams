from sentence_transformers import SentenceTransformer
from app.core.config import settings


class ServicioEmbeddings:
    """Genera vectores de embeddings usando un modelo local de sentence-transformers."""

    def __init__(self):
        self._modelo = SentenceTransformer(settings.embedding_model)

    def generar(self, texto: str) -> list[float]:
        """Genera el embedding de un texto."""
        return self._modelo.encode(texto).tolist()

    def generar_lote(self, textos: list[str]) -> list[list[float]]:
        """Genera embeddings para una lista de textos."""
        return self._modelo.encode(textos).tolist()

    @property
    def nombre_modelo(self) -> str:
        """Nombre del modelo de embeddings configurado."""
        return settings.embedding_model

    @property
    def dimensiones(self) -> int:
        """Dimensión del vector de embedding."""
        return self._modelo.get_sentence_embedding_dimension()
