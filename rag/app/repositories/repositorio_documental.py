import os
import shutil
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.models.documento import Documento
from app.models.fragmento_documental import FragmentoDocumental
from app.models.embedding import Embedding
from app.core.config import settings


class RepositorioDocumental:
    """Gestiona el almacenamiento físico de documentos y su registro en BD."""

    def __init__(self, db: Session):
        self.db = db
        os.makedirs(settings.documents_path, exist_ok=True)

    def guardar_archivo(self, file: UploadFile) -> str:
        ruta = os.path.join(settings.documents_path, file.filename)
        with open(ruta, "wb") as f:
            shutil.copyfileobj(file.file, f)
        return ruta

    def registrar_documento(self, nombre: str, ruta: str, tipo_mime: str, tamano: int) -> Documento:
        doc = Documento(
            nombre=nombre,
            ruta_almacenamiento=ruta,
            tipo_mime=tipo_mime,
            tamano_bytes=tamano,
            estado="procesando",
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def registrar_fragmento(self, documento_id: int, contenido: str, numero: int, chroma_id: str) -> FragmentoDocumental:
        fragmento = FragmentoDocumental(
            documento_id=documento_id,
            contenido=contenido,
            numero_fragmento=numero,
            chroma_id=chroma_id,
        )
        self.db.add(fragmento)
        self.db.commit()
        self.db.refresh(fragmento)
        return fragmento

    def registrar_embedding(self, fragmento_id: int, modelo: str, dimensiones: int) -> Embedding:
        emb = Embedding(
            fragmento_id=fragmento_id,
            modelo_embedding=modelo,
            dimensiones=dimensiones,
        )
        self.db.add(emb)
        self.db.commit()
        return emb

    def marcar_documento_indexado(self, documento_id: int) -> None:
        doc = self.db.query(Documento).filter(Documento.id == documento_id).first()
        if doc:
            doc.estado = "indexado"
            self.db.commit()

    def listar_documentos(self) -> list[Documento]:
        return self.db.query(Documento).order_by(Documento.fecha_subida.desc()).all()

    def obtener_documento_por_id(self, documento_id: int) -> Documento | None:
        return self.db.query(Documento).filter(Documento.id == documento_id).first()

    def archivo_existe(self, nombre: str) -> bool:
        return os.path.exists(os.path.join(settings.documents_path, nombre))
