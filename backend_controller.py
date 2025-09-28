# backend_controller.py (Arquitectura Rolls-Royce - Búsqueda y Lectura Corregidas)
import json
import os
import re

import chromadb
from chromadb.utils import embedding_functions

import analyzer
# Importaciones de nuestros módulos
from config import COLLECTION_NAME, DB_PATH, EMBEDDING_MODEL_NAME, PROMPTS_PATH
from extractor import extract_text_from_document
from gemini_provider import setup_gemini
from text_cleaner import clean_and_normalize_text
from text_scraper import extract_text_from_url

METADATA_STORE_PATH = os.path.join(DB_PATH, "metadata_store.json")

class RAGSystem:
    def __init__(self):
        print("Iniciando el Sistema RAG 'Rolls-Royce'...")
        try:
            models = setup_gemini(); self.generation_model = models["generation_model"]
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            self.embedding_function = embedding_functions.GoogleGenerativeAiEmbeddingFunction(api_key=gemini_api_key, model_name=EMBEDDING_MODEL_NAME)
            os.makedirs(DB_PATH, exist_ok=True)
            self.client = chromadb.PersistentClient(path=DB_PATH)
            self.collection = self.client.get_or_create_collection(name=COLLECTION_NAME, embedding_function=self.embedding_function)
            print(f"✅ Conectado a la colección '{COLLECTION_NAME}'.")
            self.metadata_store = self._load_metadata_store()
            print(f"✅ Almacén de metadatos cargado. {len(self.metadata_store)} documentos catalogados.")
            self.prompts_path = PROMPTS_PATH; os.makedirs(self.prompts_path, exist_ok=True)
            print(f"✅ Directorio de prompts listo.")
        except Exception as e:
            print(f"❌ Error fatal durante la inicialización: {e}"); raise

    def _load_metadata_store(self):
        if os.path.exists(METADATA_STORE_PATH):
            with open(METADATA_STORE_PATH, 'r', encoding='utf-8') as f: return json.load(f)
        return {}

    def _save_metadata_store(self):
        with open(METADATA_STORE_PATH, 'w', encoding='utf-8') as f: json.dump(self.metadata_store, f, indent=4, ensure_ascii=False)

    def _get_master_index(self, source: str):
        return self.metadata_store.get(source)

    def add_document_pipeline(self, source: str) -> dict:
        filename = os.path.basename(source)
        print(f"--- Ingesta [1/4]: Extrayendo texto de '{filename}' ---")
        extracted_content = extract_text_from_document(source) if os.path.isfile(source) else extract_text_from_url(source)
        if not extracted_content: return {"success": False, "message": "No se pudo extraer texto."}

        full_text = "\n\n".join(extracted_content) if isinstance(extracted_content, list) else extracted_content
        
        print(f"--- Ingesta [2/4]: Limpiando y generando Índice Maestro ---")
        cleaned_text = clean_and_normalize_text(full_text)
        if len(cleaned_text) < 500: return {"success": False, "message": "El documento tiene muy poco contenido útil."}

        master_index = analyzer.create_master_index(cleaned_text, filename)
        if not master_index: return {"success": False, "message": "La IA no pudo generar un Índice Maestro."}
        
        print(f"--- Ingesta [3/4]: Guardando Índice Maestro ---")
        self.metadata_store[source] = master_index
        self._save_metadata_store()

        print(f"--- Ingesta [4/4]: Embedding por Páginas/Fragmentos ---")
        if isinstance(extracted_content, list):
            chunks = [clean_and_normalize_text(page) for page in extracted_content if page.strip()]
        else:
            chunk_size = 3000; chunk_overlap = 300
            chunks = [cleaned_text[i:i + chunk_size] for i in range(0, len(cleaned_text), chunk_size - chunk_overlap)]

        if not chunks: return {"success": False, "message": "No se pudieron generar fragmentos para embedding."}

        doc_title = master_index.get('titulo', filename)
        metadatas = [{'source': source, 'doc_title': doc_title, 'fragment_num': i+1} for i, _ in enumerate(chunks)]
        ids = [f"{source}_{i}" for i in range(len(chunks))]

        batch_size = 32
        total_chunks = len(chunks)
        try:
            print(f"  -> Añadiendo {total_chunks} fragmentos a la base de datos...")
            for i in range(0, total_chunks, batch_size):
                batch_end = min(i + batch_size, total_chunks)
                self.collection.add(documents=chunks[i:batch_end], metadatas=metadatas[i:batch_end], ids=ids[i:batch_end])
            message = f"✅ Documento '{doc_title}' procesado con {total_chunks} fragmentos."
            return {"success": True, "message": message}
        except Exception as e:
            return {"success": False, "message": f"❌ Error al guardar en DB: {e}"}

    def query_document_pipeline(self, question: str, document_id: str, prompt_name: str, conversation_history: list = []) -> tuple[str, str, list]:
        print(f"--- Consulta [1/3]: Transformando pregunta con el Índice Maestro y el Historial ---")
        master_index = self._get_master_index(document_id)
        if not master_index: return "Error: No se encontró el Índice Maestro.", "", []

        formatted_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history])
        translation_prompt = f"""
        Eres un Investigador de IA. Tu misión es analizar la pregunta de un usuario y, utilizando el mapa de un libro (Índice Maestro) y el historial de la conversación, generar un plan de búsqueda HÍBRIDO.
        **ÍNDICE MAESTRO DEL DOCUMENTO:**
        ---
        {json.dumps(master_index, indent=2, ensure_ascii=False)}
        ---
        **HISTORIAL DE LA CONVERSACIÓN:**
        ---
        {formatted_history}
        ---
        **PREGUNTA MÁS RECIENTE DEL USUARIO:**
        ---
        "{question}"
        ---
        **TU TAREA:**
        1.  **Genera Consultas Semánticas:** Crea 1 o 2 consultas de búsqueda optimizadas.
        2.  **Extrae Palabras Clave:** Identifica de 2 a 4 términos específicos y cruciales.
        **FORMATO DE SALIDA (JSON):**
        ```json
        {{
          "optimized_queries": ["Consulta optimizada 1"],
          "keywords": ["Keyword1", "Keyword2"]
        }}
        ```
        """
        
        print("  -> Pidiendo a la IA que genere un plan de búsqueda híbrido...")
        response_text = self.generation_model.generate_content(translation_prompt).text
        
        try:
            search_plan_json = json.loads(re.search(r'```json\s*([\s\S]*?)\s*```', response_text).group(1))
            optimized_queries = search_plan_json.get("optimized_queries", [question])
            keywords = search_plan_json.get("keywords", [])
        except Exception:
            print("  -> ⚠️ Advertencia: La IA no devolvió un plan de búsqueda válido. Usando búsqueda simple.")
            optimized_queries = [question]
            keywords = []

        print(f"--- Consulta [2/3]: Realizando búsqueda híbrida ---")
        hybrid_queries = []
        for query in optimized_queries:
            if keywords:
                keyword_string = ", ".join(keywords)
                hybrid_query = f"{query}. Conceptos y entidades clave: {keyword_string}"
                hybrid_queries.append(hybrid_query)
            else:
                hybrid_queries.append(query)
        
        print(f"  -> Consultas para embedding: {hybrid_queries}")

        try:
            results = self.collection.query(query_texts=hybrid_queries, n_results=5, where={"source": document_id})
        except Exception as e: return f"Error al consultar DB: {e}", "", []
        
        if not results['documents'] or not results['documents'][0]: return "No se encontró contexto relevante con la búsqueda optimizada.", "", []
        
        # --- LÍNEA CORREGIDA ---
        # Ya no buscamos 'parent_text'. El contexto son los documentos recuperados directamente.
        context = "\n---\n".join(results['documents'][0])
        
        print("--- Consulta [3/3]: Sintetizando la respuesta final ---")
        prompt_template = self.get_prompt_content(prompt_name)
        if not prompt_template: return "Error: No se pudo cargar la personalidad.", "", []

        final_prompt = f"""
        {prompt_template}
        **Historial de la Conversación:**
        {formatted_history}
        **Fragmentos Relevantes Recuperados para la Pregunta Actual:**
        {context}
        **Pregunta Actual del Usuario:**
        {question}
        **Respuesta:**
        """
        response = self.generation_model.generate_content(final_prompt)
        clean_text = re.sub(r'\[Pg \d+\]|\[\d+\]', '', response.text).strip()
        
        return clean_text, context, [document_id]

    def get_library_summary(self) -> list[dict]:
        summaries = []
        for source, index_data in self.metadata_store.items():
            summaries.append({
                'id': source, 'titulo': index_data.get('titulo', os.path.basename(source)),
                'autor': index_data.get('autor', 'N/A'), 'fecha': index_data.get('fecha_publicacion', 'N/A'),
                'resumen': index_data.get('resumen_global', 'Sin resumen.'), 'tags': ", ".join(index_data.get('tags', []))
            })
        return summaries
            
    def delete_document(self, document_id: str) -> dict:
        try:
            if document_id in self.metadata_store:
                del self.metadata_store[document_id]
                self._save_metadata_store()
            self.collection.delete(where={"source": document_id})
            message = f"✅ Documento '{os.path.basename(document_id)}' eliminado completamente."
            return {"success": True, "message": message}
        except Exception as e:
            return {"success": False, "message": f"❌ Error al eliminar: {e}"}

    def list_prompts(self) -> list[str]:
        try:
            files = os.listdir(self.prompts_path)
            return sorted([os.path.splitext(f)[0] for f in files if f.endswith('.txt')])
        except Exception: return []

    def get_prompt_content(self, prompt_name: str) -> str | None:
        try:
            with open(os.path.join(self.prompts_path, f"{prompt_name}.txt"), 'r', encoding='utf-8') as f: return f.read()
        except Exception: return None
    
    def save_prompt(self, prompt_name: str, content: str) -> dict:
        sanitized_name = re.sub(r'[\\/*?:"<>|]', "", prompt_name).replace(" ", "_")
        if not sanitized_name: return {"success": False, "message": "Nombre inválido."}
        try:
            with open(os.path.join(self.prompts_path, f"{sanitized_name}.txt"), 'w', encoding='utf-8') as f: f.write(content)
            return {"success": True, "message": f"✅ Prompt '{sanitized_name}' guardado."}
        except Exception as e:
            return {"success": False, "message": f"❌ Error al guardar prompt: {e}"}