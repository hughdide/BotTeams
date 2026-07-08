import uuid
import os
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.repositories.repositorio_documental import RepositorioDocumental
from app.repositories.repositorio_vectorial import RepositorioVectorial
from app.services.servicio_embeddings import ServicioEmbeddings


CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


class ServicioProcesamientoDocumental:
    """Orquesta la carga, fragmentación e indexación de documentos."""

    def __init__(self, db: Session, repo_vectorial: RepositorioVectorial, servicio_embeddings: ServicioEmbeddings):
        self.repo_doc = RepositorioDocumental(db)
        self.repo_vec = repo_vectorial
        self.embeddings = servicio_embeddings

    def procesar_documento(self, file: UploadFile) -> dict:
        ruta = self.repo_doc.guardar_archivo(file)
        tamano = os.path.getsize(ruta)
        doc = self.repo_doc.registrar_documento(
            nombre=file.filename,
            ruta=ruta,
            tipo_mime=file.content_type,
            tamano=tamano,
        )

        texto = self._extraer_texto(ruta, file.content_type)
        fragmentos = self._fragmentar(texto)

        ids_chroma, textos_chroma, vecs_chroma, metas_chroma = [], [], [], []
        for i, fragmento in enumerate(fragmentos):
            chroma_id = str(uuid.uuid4())
            vec = self.embeddings.generar(fragmento)

            self.repo_doc.registrar_fragmento(
                documento_id=doc.id,
                contenido=fragmento,
                numero=i,
                chroma_id=chroma_id,
            )
            ids_chroma.append(chroma_id)
            textos_chroma.append(fragmento)
            vecs_chroma.append(vec)
            metas_chroma.append({"documento_id": doc.id, "documento_nombre": file.filename, "fragmento": i})

        if ids_chroma:
            self.repo_vec.insertar_fragmentos(ids_chroma, textos_chroma, vecs_chroma, metas_chroma)
            from app.models.fragmento_documental import FragmentoDocumental
            for chroma_id in ids_chroma:
                fragmento_db = self.repo_doc.db.query(FragmentoDocumental).filter_by(chroma_id=chroma_id).first()
                if fragmento_db:
                    self.repo_doc.registrar_embedding(
                        fragmento_id=fragmento_db.id,
                        modelo=self.embeddings.nombre_modelo,
                        dimensiones=self.embeddings.dimensiones,
                    )

        self.repo_doc.marcar_documento_indexado(doc.id)

        return {"id": doc.id, "nombre": doc.nombre, "estado": "indexado", "fragmentos_creados": len(fragmentos)}

    def listar_documentos(self) -> list:
        return self.repo_doc.listar_documentos()

    def obtener_ruta(self, nombre: str) -> str | None:
        from app.core.config import settings
        import os
        ruta = os.path.join(settings.documents_path, nombre)
        return ruta if os.path.exists(ruta) else None

    def _extraer_texto(self, ruta: str, tipo_mime: str) -> str:
        if tipo_mime == "application/pdf" or ruta.endswith(".pdf"):
            return self._leer_pdf(ruta)
        with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    def _leer_pdf(self, ruta: str) -> str:
        try:
            import pypdf
            texto = []
            with open(ruta, "rb") as f:
                reader = pypdf.PdfReader(f)
                for page in reader.pages:
                    texto.append(page.extract_text() or "")
            return "\n".join(texto)
        except ImportError:
            return ""

    def _fragmentar(self, texto: str) -> list[str]:
        palabras = texto.split()
        if not palabras:
            return []
        fragmentos = []
        inicio = 0
        while inicio < len(palabras):
            fin = inicio + CHUNK_SIZE
            fragmento = " ".join(palabras[inicio:fin])
            if fragmento.strip():
                fragmentos.append(fragmento)
            inicio = fin - CHUNK_OVERLAP
        return fragmentos
