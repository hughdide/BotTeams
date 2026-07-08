from fastapi import FastAPI
from app.api.routes import documentos, consultas, cuestionarios, evaluaciones, estadisticas, conversaciones

app = FastAPI(
    title="Plataforma RAG",
    description="API para procesamiento documental, consultas semánticas y cuestionarios formativos.",
    version="1.0.0",
)

app.include_router(documentos.router)
app.include_router(consultas.router)
app.include_router(cuestionarios.router)
app.include_router(evaluaciones.router)
app.include_router(estadisticas.router)
app.include_router(conversaciones.router)


@app.get("/health", tags=["Sistema"])
def health():
    return {"status": "ok"}
