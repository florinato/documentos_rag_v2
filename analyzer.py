# analyzer.py (Versión Bibliotecario)
import json
import os
import re

from gemini_provider import setup_gemini

try:
    models = setup_gemini()
    generation_model = models["generation_model"]
except Exception as e:
    print(f"❌ ANALYZER: Error fatal al inicializar Gemini: {e}")
    generation_model = None

def analyze_with_gemini(tema: str, text: str) -> dict | None:
    """
    Usa Gemini para analizar un texto y extraer metadata bibliográfica.
    """
    if not generation_model:
        return None

    prompt = f"""
    Eres un Bibliotecario de Investigación experto. Tu tarea es analizar el texto de un documento y extraer sus datos bibliográficos clave.

    PROCESO A SEGUIR:
    1.  **Analizar Contenido:** Lee el "Contenido del Documento" para identificar su estructura y datos.
    2.  **Extraer Metadatos:** Basándote en el contenido, completa los siguientes campos:
        -   "titulo": El título completo y formal del documento.
        -   "autor": El autor o autores principales. Si no se menciona, devuelve "No disponible".
        -   "fecha_publicacion": El año o la fecha de publicación original. Si no se encuentra, devuelve "No disponible".
        -   "fuente_original": La editorial, institución o revista que lo publicó. Si no se encuentra, devuelve "No disponible".
        -   "resumen": Un resumen conciso de 2-4 frases sobre el propósito y contenido del documento.
        -   "tags": De 3 a 5 palabras clave o conceptos fundamentales tratados en el texto.

    REGLAS DE SALIDA:
    - Tu respuesta DEBE ser un único bloque de código JSON.
    - Si un campo no se puede determinar a partir del texto, DEBES usar el valor "No disponible". NO inventes información.

    ---
    Tema/Nombre de archivo (para contexto): "{tema}"
    ---
    Contenido del Documento (primeros 6000 caracteres):
    "{text[:6000]}"
    ---

    RESPUESTA JSON:
    ```json
    {{
      "titulo": "...",
      "autor": "...",
      "fecha_publicacion": "...",
      "fuente_original": "...",
      "resumen": "...",
      "tags": ["tag1", "tag2", "tag3"]
    }}
    ```
    """
    try:
        print("  -> Analyzer: Solicitando extracción de datos bibliográficos a Gemini...")
        response = generation_model.generate_content(prompt)
        
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response.text)
        if not json_match:
            print("  -> ⚠️ Analyzer: No se encontró un bloque JSON en la respuesta de la IA.")
            return None

        json_str = json_match.group(1)
        analysis_result = json.loads(json_str)
        
        print("  -> ✅ Analyzer: Datos bibliográficos extraídos exitosamente.")
        return analysis_result

    except json.JSONDecodeError as e:
        print(f"  -> ❌ Analyzer: Error decodificando el JSON de la respuesta: {e}")
        return None
    except Exception as e:
        print(f"  -> ❌ Analyzer: Error inesperado durante el análisis: {e}")
        return None