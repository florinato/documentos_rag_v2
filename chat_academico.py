# chat_academico.py
import os
import re

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from gemini_provider import setup_gemini

COLLECTION_NAME = "personal_rag_collection"
DB_PATH = "bd_vectorial"

def query_rag_with_memory(question: str, history: list, n_results: int = 5):
    """
    Realiza una consulta al RAG, utilizando el historial de la conversación
    para entender el contexto y dar una respuesta académica y precisa.
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

    # --- EL PROMPT ACADÉMICO CON MEMORIA ---
    # Convertimos el historial en una cadena de texto para el prompt
    formatted_history = "\n".join(history)

    prompt = f"""
    Eres un "Asistente Académico y Documental". Tu función es resumir, aclarar y explicar conceptos basándote ESTRICTAMENTE en el "Contexto" y en la "Conversación Anterior".

    REGLAS:
    1.  **Sé directo, claro y objetivo:** Cíñete a los hechos del texto.
    2.  **Usa la Memoria:** Utiliza la "Conversación Anterior" para entender preguntas de seguimiento (ej: 'explica el segundo punto', '¿a quién se refiere?', 'dame más detalles sobre eso').
    3.  **Fidelidad al Contexto:** Basa tu respuesta 100% en la información proporcionada. No añadas información externa.
    4.  **Limpieza:** Elimina cualquier referencia de página `[Pg ##]` y números de nota.
    5.  **Salida de Emergencia:** Si la respuesta no se encuentra en el contexto, responde: "La información solicitada no se encuentra en los fragmentos del documento proporcionados."

    Conversación Anterior:
    ---
    {formatted_history}
    ---

    Contexto Relevante para la Nueva Pregunta:
    ---
    {context}
    ---

    Pregunta del Usuario: {question}

    Respuesta Académica:
    """
    
    print("\nGenerando respuesta académica...")
    response = generation_model.generate_content(prompt)

    clean_text = re.sub(r'\[Pg \d+\]|\[\d+\]', '', response.text).strip()
    
    return clean_text, context, sources


if __name__ == "__main__":
    print("\n--- Asistente Académico con Memoria ---")
    print("Chatea con tu documento. Escribe 'salir' para terminar.")

    # --- LA MEMORIA DE LA CONVERSACIÓN ---
    # Esta lista guardará el historial.
    conversation_history = []
    # Máximo de turnos a recordar (para no sobrecargar el prompt)
    MAX_HISTORY_TURNS = 3 # Recordará las últimas 3 preguntas y 3 respuestas

    while True:
        user_question = input("\nPregunta > ")
        if user_question.lower() == 'salir':
            break
        
        answer, retrieved_context, sources = query_rag_with_memory(user_question, conversation_history)
        
        print("\nRespuesta del Asistente:")
        print(answer)
        
        # Actualizamos el historial con el último turno
        conversation_history.append(f"Usuario: {user_question}")
        conversation_history.append(f"Asistente: {answer}")

        # Mantenemos el historial con un tamaño manejable
        if len(conversation_history) > MAX_HISTORY_TURNS * 2:
            conversation_history = conversation_history[-(MAX_HISTORY_TURNS * 2):]

        print("\n" + "="*50)
        print("FRAGMENTOS CONSULTADOS PARA ESTA RESPUESTA:")
        print("="*50)
        if sources:
            print(f"Fuentes: {sources}\n")
            print(retrieved_context)
        else:
            print("No se recuperó ningún contexto.")
        print("="*50)