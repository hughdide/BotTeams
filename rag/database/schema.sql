-- Schema principal de la base de datos operacional

CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    rol VARCHAR(50) DEFAULT 'empleado',
    fecha_creacion TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS documentos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    ruta_almacenamiento VARCHAR(500) NOT NULL,
    tipo_mime VARCHAR(100),
    tamano_bytes INTEGER,
    estado VARCHAR(50) DEFAULT 'pendiente',
    fecha_subida TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fragmentos_documentales (
    id SERIAL PRIMARY KEY,
    documento_id INTEGER REFERENCES documentos(id) ON DELETE CASCADE,
    contenido TEXT NOT NULL,
    numero_fragmento INTEGER,
    chroma_id VARCHAR(255) UNIQUE,
    fecha_creacion TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS embeddings (
    id SERIAL PRIMARY KEY,
    fragmento_id INTEGER REFERENCES fragmentos_documentales(id) ON DELETE CASCADE,
    modelo_embedding VARCHAR(255),
    dimensiones INTEGER,
    fecha_creacion TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS consultas (
    id SERIAL PRIMARY KEY,
    usuario_id VARCHAR(255),
    usuario_nombre VARCHAR(255),
    pregunta TEXT NOT NULL,
    conversation_reference JSONB,
    fecha TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS respuestas (
    id SERIAL PRIMARY KEY,
    consulta_id INTEGER REFERENCES consultas(id) ON DELETE CASCADE,
    respuesta TEXT NOT NULL,
    fragmentos_usados JSONB,
    fecha TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cuestionarios (
    id SERIAL PRIMARY KEY,
    pregunta TEXT NOT NULL,
    respuesta_correcta TEXT NOT NULL,
    tema VARCHAR(255),
    fecha TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS respuestas_cuestionario (
    id SERIAL PRIMARY KEY,
    empleado_id VARCHAR(255),
    empleado_nombre VARCHAR(255),
    cuestionario_id INTEGER REFERENCES cuestionarios(id),
    respuesta TEXT NOT NULL,
    score VARCHAR(50),
    feedback TEXT,
    fecha TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS conversaciones (
    id SERIAL PRIMARY KEY,
    empleado_id VARCHAR(255) UNIQUE,
    empleado_nombre VARCHAR(255),
    conversation_reference JSONB,
    fecha_actualizacion TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cuestionarios_activos (
    id SERIAL PRIMARY KEY,
    empleado_id VARCHAR(255) UNIQUE,
    cuestionario_id INTEGER REFERENCES cuestionarios(id),
    fecha TIMESTAMP DEFAULT NOW()
);
