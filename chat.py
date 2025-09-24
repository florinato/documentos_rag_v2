# chat.py
import os
import re

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from gemini_provider import setup_gemini

COLLECTION_NAME = "personal_rag_collection"
DB_PATH = "bd_vectorial"

def query_rag(question: str, n_results: int = 5):
    """
    Realiza una consulta y genera una respuesta sabia y elocuente,
    interpretando y conectando las ideas del contexto.
    """
    try:
        models = setup_gemini()
        generation_model = models["generation_model"]
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        google_ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(api_key=gemini_api_key)
        
        client = chromadb.PersistentClient(path=DB_PATH, settings=Settings(anonymized_telemetry=False))
        
        collection = client.get_collection(name=COLLECTION_NAME, embedding_function=google_ef)
    
    except Exception as e:
        return f"Error: {e}. Asegúrate de haber ejecutado 'add_to_database.py' primero.", "", []

    results = collection.query(query_texts=[question], n_results=n_results)
    
    if not results['documents'] or not results['documents'][0]:
        return "No se encontró contexto relevante para esta pregunta.", "", []

    context = "\n---\n".join(results['documents'][0])
    sources = list(set([meta['source'] for meta in results['metadatas'][0]]))

    # --- EL PROMPT DEFINITIVO: MODO MAESTRO DE SABIDURÍA ---
    prompt = f"""
    Eres un "Maestro de Sabiduría". Tu especialidad es el tratado "La Historia de la Magia". Respondes a las preguntas con elocuencia, profundidad y una prosa elegante, como si hubieras interiorizado completamente el conocimiento del libro.

    PROCESO A SEGUIR:
    1.  **Análisis Interno:** Lee la "Pregunta del Usuario" y extrae mentalmente las ideas y argumentos clave del "Contexto" que la responden.
    2.  **Síntesis Elocuente:** Usando las ideas extraídas, redacta una respuesta fluida y natural. Hila los conceptos, interpreta las conexiones entre ellos y presenta el conocimiento de una forma sabia y coherente. Tu estilo de escritura debe ser rico y filosófico.
    3.  **Verificación Final:** Relee tu respuesta y asegúrate de que, aunque interpretativa y bien escrita, no contiene NINGUNA información que no pueda ser respaldada por los fragmentos proporcionados.

    REGLAS FINALES:
    - **Cero Invención:** Tu libertad es para interpretar y conectar ideas del texto, no para crear información nueva.
    - **Limpieza Impecable:** Elimina por completo todas las referencias de página `[Pg ##]` y notas `[##]`.
    - **Conclusión Satisfactoria:** La respuesta debe sentirse completa y profunda, sin finales abruptos.
    - **Salida de Emergencia:** Si el contexto es insuficiente, indícalo con elegancia: "Aunque el tratado aborda temas vastos, los fragmentos recuperados no contienen la profundidad necesaria para responder a tu pregunta."

    Contexto Proporcionado:
    ---
    {context}
    ---

    Pregunta del Usuario: {question}

    Respuesta del Maestro de Sabiduría:
    """
    
    print("\nConsultando al Maestro de Sabiduría...")
    response = generation_model.generate_content(prompt)

    # Limpieza final para asegurar la calidad
    clean_text = re.sub(r'\[Pg \d+\]|\[\d+\]', '', response.text).strip()
    
    return clean_text, context, sources


if __name__ == "__main__":
    print("\n--- Guía Mágico del Tratado ---")
    print("Conectado al conocimiento del documento. Escribe 'salir' para terminar.")

    while True:
        user_question = input("\nPregunta > ")
        if user_question.lower() == 'salir':
            break
        
        answer, retrieved_context, sources = query_rag(user_question)
        
        print("\nRespuesta del Guía:")
        print(answer)
        
        print("\n" + "="*50)
        print("FRAGMENTOS DEL TRATADO CONSULTADOS:")
        print("="*50)
        if sources:
            print(f"Fuentes: {sources}\n")
            print(retrieved_context)
        else:
            print("No se recuperó ningún contexto.")
        print("="*50)