# backend_controller.py
import os
import re

import chromadb
from chromadb.utils import embedding_functions

import analyzer
from chunker import create_child_chunks, create_parent_chunks
# Importaciones de nuestros módulos
from config import COLLECTION_NAME, DB_PATH, EMBEDDING_MODEL_NAME, PROMPTS_PATH
from extractor import extract_text_from_document
from gemini_provider import setup_gemini
from text_scraper import extract_text_from_url


class RAGSystem:
    def __init__(self):
        print("Iniciando el Sistema RAG del Gurú...")
        try:
            models = setup_gemini()
            self.generation_model = models["generation_model"]
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            self.embedding_function = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
                api_key=gemini_api_key, model_name=EMBEDDING_MODEL_NAME
            )
            self.client = chromadb.PersistentClient(path=DB_PATH)
            self.collection = self.client.get_or_create_collection(
                name=COLLECTION_NAME, embedding_function=self.embedding_function
            )
            print(f"✅ Conectado a la colección '{COLLECTION_NAME}' en '{DB_PATH}'.")
            self.prompts_path = PROMPTS_PATH
            os.makedirs(self.prompts_path, exist_ok=True)
            print(f"✅ Directorio de prompts '{self.prompts_path}' listo.")
        except Exception as e:
            print(f"❌ Error fatal durante la inicialización: {e}")
            raise

    # --- PIPELINE - PASO 1 ---
    def extract_and_analyze(self, source: str) -> dict:
        """Extrae texto y lo analiza con IA para obtener metadatos bibliográficos."""
        tema_del_documento = os.path.basename(source)
        print(f"--- Pipeline Paso 1: Extrayendo y Analizando '{tema_del_documento}' ---")
        
        extracted_text = ""
        if source.startswith('http://') or source.startswith('https://'):
            extracted_text = extract_text_from_url(source)
        elif os.path.isfile(source):
            extracted_text = extract_text_from_document(source)
        else:
            return {"success": False, "message": f"Fuente no válida: {source}"}

        if not extracted_text or len(extracted_text) < 100:
            return {"success": False, "message": "No se pudo extraer suficiente texto legible."}
        
        analysis_data = analyzer.analyze_with_gemini(tema_del_documento, extracted_text)
        if not analysis_data:
            analysis_data = {}
            print("  -> Advertencia: El análisis con IA falló. Se continuará sin metadatos enriquecidos.")

        return {
            "success": True,
            "extracted_text": extracted_text,
            "analysis_data": analysis_data
        }

    # --- PIPELINE - PASO 2 ---
    def chunk_and_index(self, source: str, text_to_chunk: str, analysis_data: dict) -> dict:
        """Toma texto y metadatos, los chunkifica y los guarda en la base de datos."""
        doc_title = analysis_data.get('titulo', os.path.basename(source))
        print(f"--- Pipeline Paso 2: Chunkificando e Indexando '{doc_title}' ---")

        parent_chunks = create_parent_chunks(text_to_chunk)
        if not parent_chunks:
            return {"success": False, "message": "El texto no se pudo dividir en fragmentos."}

        all_child_chunks, all_metadatas, all_ids = [], [], []
        
        for i, parent_text in enumerate(parent_chunks):
            child_chunks = create_child_chunks(parent_text)
            for j, child_text in enumerate(child_chunks):
                all_child_chunks.append(child_text)
                all_metadatas.append({
                    'source': source, 
                    'parent_text': parent_text,
                    'doc_title': doc_title,
                    'doc_summary': analysis_data.get('resumen', 'No disponible'),
                    'doc_author': analysis_data.get('autor', 'No disponible'),
                    'doc_pub_date': analysis_data.get('fecha_publicacion', 'No disponible'),
                    'doc_tags': ", ".join(analysis_data.get('tags', []))
                })
                all_ids.append(f"{source}_{i}_{j}")
        
        if not all_child_chunks:
             return {"success": False, "message": "No se pudieron generar chunks hijos."}

        batch_size = 32
        total_chunks = len(all_child_chunks)
        try:
            print(f"  -> Añadiendo {total_chunks} fragmentos 'hijo' a la base de datos...")
            for i in range(0, total_chunks, batch_size):
                batch_end = min(i + batch_size, total_chunks)
                self.collection.add(
                    documents=all_child_chunks[i:batch_end],
                    metadatas=all_metadatas[i:batch_end],
                    ids=all_ids[i:batch_end]
                )
            message = f"✅ Documento '{doc_title}' indexado exitosamente."
            return {"success": True, "message": message}
        except Exception as e:
            return {"success": False, "message": f"❌ Error al guardar en DB: {e}"}

    def get_library_summary(self) -> list[dict]:
        """Devuelve una lista de diccionarios, uno por cada documento único, con sus datos bibliográficos."""
        try:
            all_metadata = self.collection.get(include=["metadatas"])['metadatas']
            documents_summary = {}
            for meta in all_metadata:
                source = meta.get('source')
                if source and source not in documents_summary:
                    documents_summary[source] = {
                        'id': source,
                        'titulo': meta.get('doc_title', os.path.basename(source)),
                        'autor': meta.get('doc_author', 'N/A'),
                        'fecha': meta.get('doc_pub_date', 'N/A'),
                        'resumen': meta.get('doc_summary', 'Sin resumen.'),
                        'tags': meta.get('doc_tags', '')
                    }
            return list(documents_summary.values())
        except Exception as e:
            print(f"❌ Error al obtener el resumen de la biblioteca: {e}")
            return []
            
    def delete_document(self, document_id: str) -> dict:
        try:
            self.collection.delete(where={"source": document_id})
            message = f"✅ Documento '{os.path.basename(document_id)}' eliminado."
            return {"success": True, "message": message}
        except Exception as e:
            return {"success": False, "message": f"❌ Error al eliminar: {e}"}

    def list_prompts(self) -> list[str]:
        try:
            files = os.listdir(self.prompts_path)
            return sorted([os.path.splitext(f)[0] for f in files if f.endswith('.txt')])
        except Exception as e: return []

    def get_prompt_content(self, prompt_name: str) -> str | None:
        try:
            with open(os.path.join(self.prompts_path, f"{prompt_name}.txt"), 'r', encoding='utf-8') as f: return f.read()
        except Exception as e: return None
    
    def save_prompt(self, prompt_name: str, content: str) -> dict:
        sanitized_name = re.sub(r'[\\/*?:"<>|]', "", prompt_name).replace(" ", "_")
        if not sanitized_name: return {"success": False, "message": "Nombre inválido."}
        try:
            with open(os.path.join(self.prompts_path, f"{sanitized_name}.txt"), 'w', encoding='utf-8') as f: f.write(content)
            return {"success": True, "message": f"✅ Prompt '{sanitized_name}' guardado."}
        except Exception as e:
            return {"success": False, "message": f"❌ Error al guardar prompt: {e}"}
            
    def query_document(self, question: str, document_id: str, prompt_name: str) -> tuple[str, str, list]:
        print(f"\nConsultando ('{prompt_name}') sobre '{os.path.basename(document_id)}'...")
        prompt_template = self.get_prompt_content(prompt_name)
        if not prompt_template: return "Error: No se pudo cargar la personalidad.", "", []
        try:
            results = self.collection.query(query_texts=[question], n_results=10, where={"source": document_id})
        except Exception as e: return f"Error al consultar DB: {e}", "", []
        if not results['metadatas'] or not results['metadatas'][0]: return "No se encontró contexto.", "", []
        
        parent_texts = [meta['parent_text'] for meta in results['metadatas'][0]]
        unique_parent_texts = list(dict.fromkeys(parent_texts))
        context = "\n---\n".join(unique_parent_texts)
        sources = [document_id]
        final_prompt = prompt_template.format(context=context, question=question)
        
        print(f"La personalidad '{prompt_name}' está meditando...")
        response = self.generation_model.generate_content(final_prompt)
        clean_text = re.sub(r'\[Pg \d+\]|\[\d+\]', '', response.text).strip()
        
        return clean_text, context, sources