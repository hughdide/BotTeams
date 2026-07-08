import time
import chromadb
from typing import List
from app.core.config import settings


class RepositorioVectorial:
    """Encapsula todas las operaciones sobre ChromaDB."""

    def __init__(self):
        self.client = self._conectar()
        self.collection = self.client.get_or_create_collection(settings.chroma_collection)

    def _conectar(self, intentos: int = 10, espera: int = 3) -> chromadb.HttpClient:
        """Intenta conectarse a ChromaDB con reintentos."""
        for i in range(intentos):
            try:
                client = chromadb.HttpClient(
                    host=settings.chroma_host,
                    port=settings.chroma_port,
                    tenant="default_tenant",
                    database="default_database",
                )
                client.heartbeat()
                return client
            except Exception:
                if i < intentos - 1:
                    time.sleep(espera)
        raise RuntimeError(f"No se pudo conectar a ChromaDB tras {intentos} intentos.")

    def insertar_fragmentos(self, ids: List[str], textos: List[str], embeddings: List[List[float]], metadatos: List[dict]) -> None:
        """Inserta fragmentos con sus embeddings y metadatos en la colección."""
        self.collection.add(
            ids=ids,
            documents=textos,
            embeddings=embeddings,
            metadatas=metadatos,
        )

    def buscar_similares(self, embedding_consulta: List[float], top_k: int = 3) -> list[dict]:
        """Devuelve los fragmentos más cercanos al embedding de la consulta."""
        resultados = self.collection.query(
            query_embeddings=[embedding_consulta],
            n_results=top_k,
        )
        fragmentos = []
        if not resultados["documents"] or not resultados["documents"][0]:
            return fragmentos
        for i, texto in enumerate(resultados["documents"][0]):
            fragmentos.append({
                "texto": texto,
                "distancia": resultados["distances"][0][i] if resultados.get("distances") else None,
                "metadata": resultados["metadatas"][0][i] if resultados.get("metadatas") else {},
            })
        return fragmentos

    def contar_documentos(self) -> int:
        """Devuelve el número total de fragmentos indexados."""
        return self.collection.count()
