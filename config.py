# config.py

# --- Configuración de la Base de Datos Vectorial ---
# Nombre del directorio donde se guardará la base de datos persistente.
DB_PATH = "biblioteca_db"

# Nombre de la colección dentro de ChromaDB.
COLLECTION_NAME = "tratados"


# --- Configuración de los Modelos de IA (Gemini) ---
# Modelo para la generación de respuestas (el chat).
GENERATION_MODEL_NAME = "models/gemini-2.0-flash-exp"

# Modelo para crear los embeddings (los vectores numéricos del texto).
EMBEDDING_MODEL_NAME = "models/embedding-001"

# --- Configuración de los Prompts ---
# Directorio donde se guardan las personalidades de la IA.
PROMPTS_PATH = "system_prompts"