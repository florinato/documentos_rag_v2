
# gemini_provider.py
import os

from dotenv import load_dotenv
from google.generativeai import GenerativeModel, configure

# Importamos la configuración centralizada
from config import EMBEDDING_MODEL_NAME, GENERATION_MODEL_NAME


def setup_gemini():
    """
    Carga la clave API desde el archivo .env e inicializa el SDK de Gemini.
    """
    load_dotenv()
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    if not gemini_api_key:
        raise ValueError("La clave API de Gemini no se encontró. Asegúrate de tener un archivo .env con 'GEMINI_API_KEY'.")

    configure(api_key=gemini_api_key)
    print(f"✅ Conexión con Gemini establecida.")
    
    return {
        "generation_model": GenerativeModel(GENERATION_MODEL_NAME),
        "embedding_model_name": EMBEDDING_MODEL_NAME  # Devolvemos solo el nombre
    }