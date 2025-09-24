# add_to_database.py
import os
import sys

import chromadb
from chromadb.config import \
    Settings  # <-- IMPORTANTE: Asegúrate de que esta línea exista
from chromadb.utils import embedding_functions

from chunker import chunk_text
from extractor import extract_text_from_document
from gemini_provider import setup_gemini
from text_scraper import extract_text_from_url

COLLECTION_NAME = "personal_rag_collection"

def main():
    if len(sys.argv) < 2:
        print("Error: Debes proporcionar una fuente de datos.")
        print("Uso: python add_to_database.py <URL_o_ruta_a_archivo>")
        sys.exit(1)
    
    source = sys.argv[1]

    try:
        setup_gemini()
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        google_ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(api_key=gemini_api_key)
    except ValueError as e:
        print(f"Error de configuración: {e}")
        exit()

    # <-- IMPORTANTE: Esta línea deshabilita la telemetría que causa el error
    client = chromadb.PersistentClient(path="bd_vectorial")
    
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=google_ef
    )
    print(f"✅ Conectado a la colección '{COLLECTION_NAME}'.")

    print(f"Procesando fuente: {source}...")
    extracted_text = ""
    if source.startswith('http://') or source.startswith('https://'):
        extracted_text = extract_text_from_url(source)
    elif os.path.isfile(source):
        extracted_text = extract_text_from_document(source)
    else:
        print(f"❌ Error: La fuente '{source}' no es una URL válida ni un archivo existente.")
        sys.exit(1)

    if not extracted_text:
        print(f"❌ No se pudo extraer texto de la fuente '{source}'.")
        sys.exit(1)

    print("Dividiendo el texto en fragmentos (chunks)...")
    chunks = chunk_text(extracted_text)

    if not chunks:
        print("❌ El texto extraído estaba vacío o no se pudo dividir.")
        sys.exit(1)
        
    base_id = os.path.basename(source)
    ids = [f"{base_id}_{i}" for i in range(len(chunks))]
    metadatas = [{'source': source} for _ in range(len(chunks))]

    print(f"Añadiendo {len(chunks)} fragmentos a la base de datos vectorial...")
    try:
        collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        print(f"✅ Documento '{source}' procesado y añadido exitosamente a la base de datos.")
    except Exception as e:
        print(f"❌ Ocurrió un error al añadir los documentos a ChromaDB: {e}")

if __name__ == "__main__":
    main()