from fastapi import FastAPI, UploadFile, File, Header, HTTPException
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.anthropic import Anthropic
from fastapi.responses import FileResponse
import chromadb
import psycopg2
import os
import shutil
import random

# Embeddings locales sin API key
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
Settings.llm = Anthropic(
    model="claude-haiku-4-5-20251001",
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

app = FastAPI()

API_KEY = os.getenv("API_KEY", "changeme")

def verify_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API Key inválida")

def get_db():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        database="botformacion",
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )

# Conexión a ChromaDB
chroma_client = chromadb.HttpClient(host="chromadb", port=8000)
collection = chroma_client.get_or_create_collection("empresa_docs")
vector_store = ChromaVectorStore(chroma_collection=collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...), x_api_key: str = Header(...)):
    verify_key(x_api_key)
    os.makedirs("/app/documents", exist_ok=True)
    path = f"/app/documents/{file.filename}"
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    docs = SimpleDirectoryReader(input_files=[path]).load_data()
    VectorStoreIndex.from_documents(docs, storage_context=storage_context)
    return {"status": "indexado", "archivo": file.filename}

@app.post("/query")
async def query(body: dict, x_api_key: str = Header(...)):
    verify_key(x_api_key)

    # Debug - verificar que el LLM está cargado
    print(f"LLM: {Settings.llm}")
    print(f"Pregunta: {body['pregunta']}")

    index = VectorStoreIndex.from_vector_store(
        vector_store,
        embed_model=Settings.embed_model
    )

    # Recuperar fragmentos relevantes
    retriever = index.as_retriever(similarity_top_k=3)
    nodos = retriever.retrieve(body["pregunta"])

    print(f"Nodos encontrados: {len(nodos)}")
    for n in nodos:
        print(f"Fragmento: {n.text}")

    if not nodos or all(n.score < 0.3 for n in nodos):
        return {"respuesta": "No encontré información relevante en los documentos de la empresa. Prueba a preguntar algo relacionado con los documentos disponibles."}

    # Construir contexto y llamar al LLM directamente
    contexto = "\n".join([n.text for n in nodos])
    prompt = f"""Eres el asistente interno de la empresa. Basándote SOLO en este contexto:
{contexto}

Si la pregunta no tiene relación con el contexto, responde exactamente: "No tengo información sobre ese tema en los documentos de la empresa."

Responde en español esta pregunta: {body["pregunta"]}"""

    respuesta = Settings.llm.complete(prompt)
    return {"respuesta": str(respuesta)}

@app.post("/generate-quiz")
async def generate_quiz(x_api_key: str = Header(...), body: dict = {}):
    verify_key(x_api_key)
    
    index = VectorStoreIndex.from_vector_store(
        vector_store, embed_model=Settings.embed_model)
    retriever = index.as_retriever(similarity_top_k=5)
    
    # Si viene tema personalizado lo usamos, si no uno aleatorio
    tema = body.get("tema") if body else None
    if not tema:
        temas = ["procedimientos", "políticas", "normas", "empresa", "empleados"]
        tema = random.choice(temas)
    
    nodos = retriever.retrieve(tema)
    
    if not nodos:
        raise HTTPException(status_code=404, detail="No hay documentos indexados")
    
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT pregunta FROM quizzes ORDER BY fecha DESC LIMIT 5")
    ultimas = [r[0] for r in cur.fetchall()]
    cur.close()
    db.close()
    
    contexto = "\n".join([n.text for n in nodos])
    ultimas_str = "\n".join(ultimas) if ultimas else "Ninguna"
    
    prompt = f"""Basándote en este contenido de la empresa:
{contexto}

Preguntas ya realizadas (NO repitas):
{ultimas_str}

Genera UNA pregunta sobre el tema: "{tema}"
Responde ÚNICAMENTE con este JSON sin texto adicional:
{{"pregunta": "la pregunta aquí", "respuesta_correcta": "la respuesta correcta aquí"}}"""
    
    resultado = Settings.llm.complete(prompt)
    texto = str(resultado).strip()
    
    import re
    match = re.search(r'\{.*?\}', texto, re.DOTALL)
    if not match:
        raise HTTPException(status_code=500, detail="No se pudo parsear la respuesta")
    
    import json
    data = json.loads(match.group())
    
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO quizzes (pregunta, respuesta_correcta) VALUES (%s, %s) RETURNING id",
        (data["pregunta"], data["respuesta_correcta"])
    )
    quiz_id = cur.fetchone()[0]
    db.commit()
    cur.close()
    db.close()
    
    return {"quiz_id": quiz_id, "pregunta": data["pregunta"]}

@app.post("/evaluate-answer")
async def evaluate_answer(body: dict, x_api_key: str = Header(...)):
    verify_key(x_api_key)
    
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT pregunta, respuesta_correcta FROM quizzes WHERE id = %s", 
                (body["quiz_id"],))
    quiz = cur.fetchone()
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz no encontrado")
    
    pregunta, respuesta_correcta = quiz
    
    prompt = f"""Evalúa esta respuesta de un empleado:
Pregunta: {pregunta}
Respuesta correcta: {respuesta_correcta}
Respuesta del empleado: {body["respuesta"]}

Responde ÚNICAMENTE con este JSON sin texto adicional:
{{"score": "correcto|parcial|incorrecto", "feedback": "explicación breve en español"}}"""
    
    resultado = Settings.llm.complete(prompt)
    texto = str(resultado).strip()
    
    import re
    match = re.search(r'\{.*?\}', texto, re.DOTALL)
    if not match:
        raise HTTPException(status_code=500, detail="No se pudo parsear la evaluación")
    
    import json
    data = json.loads(match.group())
    
    cur.execute(
        """INSERT INTO respuestas 
        (empleado_id, empleado_nombre, quiz_id, respuesta, score, feedback) 
        VALUES (%s, %s, %s, %s, %s, %s)""",
        (body["empleado_id"], body["empleado_nombre"], 
         body["quiz_id"], body["respuesta"], 
         data["score"], data["feedback"])
    )
    db.commit()
    cur.close()
    db.close()
    
    return {
        "score": data["score"],
        "feedback": data["feedback"],
        "respuesta_correcta": respuesta_correcta
    }

@app.post("/conversaciones/guardar")
async def guardar_conversacion(body: dict, x_api_key: str = Header(...)):
    verify_key(x_api_key)
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        INSERT INTO conversaciones (empleado_id, empleado_nombre, conversation_reference)
        VALUES (%s, %s, %s::jsonb)
        ON CONFLICT (empleado_id) DO UPDATE 
        SET conversation_reference = %s::jsonb,
            empleado_nombre = %s
        """,
        (body["empleado_id"], body["empleado_nombre"], 
         body["conversation_reference"],
         body["conversation_reference"],
         body["empleado_nombre"])
    )
    db.commit()
    cur.close()
    db.close()
    return {"status": "ok"}

@app.get("/conversaciones")
async def get_conversaciones(x_api_key: str = Header(...)):
    verify_key(x_api_key)
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT empleado_id, empleado_nombre, conversation_reference FROM conversaciones")
    rows = cur.fetchall()
    cur.close()
    db.close()
    return [{"empleado_id": r[0], "empleado_nombre": r[1], "conversation_reference": r[2]} for r in rows]

@app.post("/quizzes-activos/guardar")
async def guardar_quiz_activo(body: dict, x_api_key: str = Header(...)):
    verify_key(x_api_key)
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        INSERT INTO quizzes_activos (empleado_id, quiz_id)
        VALUES (%s, %s)
        ON CONFLICT (empleado_id) DO UPDATE SET quiz_id = %s, fecha = NOW()
        """,
        (body["empleado_id"], body["quiz_id"], body["quiz_id"])
    )
    db.commit()
    cur.close()
    db.close()
    return {"status": "ok"}

@app.get("/quizzes-activos/{empleado_id}")
async def get_quiz_activo(empleado_id: str, x_api_key: str = Header(...)):
    verify_key(x_api_key)
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT quiz_id FROM quizzes_activos WHERE empleado_id = %s", (empleado_id,))
    row = cur.fetchone()
    cur.close()
    db.close()
    if not row:
        raise HTTPException(status_code=404, detail="No hay quiz activo")
    return {"quiz_id": row[0]}

@app.delete("/quizzes-activos/{empleado_id}")
async def eliminar_quiz_activo(empleado_id: str, x_api_key: str = Header(...)):
    verify_key(x_api_key)
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM quizzes_activos WHERE empleado_id = %s", (empleado_id,))
    db.commit()
    cur.close()
    db.close()
    return {"status": "ok"}

@app.get("/estadisticas")
async def get_estadisticas(x_api_key: str = Header(...)):
    verify_key(x_api_key)
    db = get_db()
    cur = db.cursor()
    
    # Resultados por empleado
    cur.execute("""
        SELECT 
            r.empleado_nombre,
            COUNT(*) as total_respuestas,
            SUM(CASE WHEN r.score = 'correcto' THEN 1 ELSE 0 END) as correctas,
            SUM(CASE WHEN r.score = 'parcial' THEN 1 ELSE 0 END) as parciales,
            SUM(CASE WHEN r.score = 'incorrecto' THEN 1 ELSE 0 END) as incorrectas
        FROM respuestas r
        GROUP BY r.empleado_nombre
        ORDER BY correctas DESC
    """)
    empleados = cur.fetchall()
    
    # Ultimas respuestas
    cur.execute("""
        SELECT 
            r.empleado_nombre,
            q.pregunta,
            r.respuesta,
            r.score,
            r.feedback,
            r.fecha
        FROM respuestas r
        JOIN quizzes q ON r.quiz_id = q.id
        ORDER BY r.fecha DESC
        LIMIT 20
    """)
    ultimas = cur.fetchall()
    
    cur.close()
    db.close()
    
    return {
        "empleados": [
            {
                "nombre": r[0],
                "total": r[1],
                "correctas": r[2],
                "parciales": r[3],
                "incorrectas": r[4],
                "porcentaje": round((r[2] / r[1]) * 100, 1) if r[1] > 0 else 0
            }
            for r in empleados
        ],
        "ultimas_respuestas": [
            {
                "empleado": r[0],
                "pregunta": r[1],
                "respuesta": r[2],
                "score": r[3],
                "feedback": r[4],
                "fecha": r[5].isoformat()
            }
            for r in ultimas
        ]
    }

@app.get("/documentos")
async def listar_documentos(x_api_key: str = Header(...)):
    verify_key(x_api_key)
    documentos = []
    if os.path.exists("/app/documents"):
        documentos = os.listdir("/app/documents")
    return {"documentos": documentos}

@app.get("/documentos/{nombre}")
async def descargar_documento(nombre: str, x_api_key: str = Header(...)):
    verify_key(x_api_key)
    path = f"/app/documents/{nombre}"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return FileResponse(path, filename=nombre)
