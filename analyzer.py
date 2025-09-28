# analyzer.py (Versión Final - Índice Maestro Holístico)
import json
import re

from gemini_provider import setup_gemini

try:
    models = setup_gemini()
    generation_model = models["generation_model"]
except Exception as e:
    print(f"❌ ANALYZER: Error fatal al inicializar Gemini: {e}")
    generation_model = None

def create_master_index(full_text: str, filename: str) -> dict | None:
    """
    Analiza un documento de forma holística para crear un "Índice Maestro" detallado,
    aprovechando una gran ventana de contexto.
    """
    if not generation_model: return None

    # Límite seguro para no exceder la cuota de tokens por minuto en una sola llamada.
    # 200,000 caracteres son ~50,000 tokens, muy por debajo del límite de 250,000 TPM.
    # Esto es suficiente para la mayoría de documentos o las partes más importantes.
    MAX_CHARS_FOR_ANALYSIS = 200000
    text_sample = full_text[:MAX_CHARS_FOR_ANALYSIS]

    prompt = f"""
    Eres un Editor Senior y un Agente de Catalogación de IA. Tu misión es analizar el siguiente documento para crear un "Índice Maestro" en formato JSON.

    PROCESO A SEGUIR:
    1.  **Datos Bibliográficos:** Busca en el texto para encontrar el título completo, autor(es), y fecha de publicación.
    2.  **Resumen Global:** Escribe un resumen de 3-5 frases que capture la tesis y el contenido principal del documento.
    3.  **Índice Estructurado:** Identifica la tabla de contenidos o la estructura de capítulos/secciones. Crea un mapa donde cada clave sea el nombre del capítulo/sección y el valor sea un resumen de una sola frase de su contenido. Si no hay capítulos claros, crea secciones lógicas (ej: "Introducción", "Desarrollo del Tema Principal", "Conclusiones").
    4.  **Temas Fundamentales:** Extrae de 5 a 7 'tags' que representen los conceptos clave del documento.

    REGLAS IMPORTANTES:
    - Analiza el texto proporcionado de forma completa para encontrar la información.
    - Si un campo no se puede determinar, usa el valor "No disponible". NO inventes información.
    - El formato de salida DEBE ser un único bloque de código JSON válido.

    ---
    Nombre de Archivo (para contexto): "{filename}"
    ---
    Contenido del Documento (hasta {MAX_CHARS_FOR_ANALYSIS} caracteres):
    "{text_sample}"
    ---

    RESPUESTA JSON (Índice Maestro):
    ```json
    {{
      "titulo": "...",
      "autor": "...",
      "fecha_publicacion": "...",
      "resumen_global": "...",
      "indice_estructurado": {{
        "Capítulo 1: Nombre del Capítulo": "Resumen de una frase de este capítulo.",
        "Capítulo 2: Otro Nombre": "Resumen de una frase de este otro capítulo."
      }},
      "tags": ["tag1", "tag2", "tag3"]
    }}
    ```
    """
    try:
        print(f"  -> Analyzer: Enviando {len(text_sample)} caracteres a Gemini para generar el Índice Maestro...")
        response = generation_model.generate_content(prompt)
        
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response.text)
        if not json_match:
            print("  -> ⚠️ Analyzer: No se encontró un bloque JSON en la respuesta de la IA.")
            return None

        json_str = json_match.group(1)
        analysis_result = json.loads(json_str)
        
        print("  -> ✅ Analyzer: Índice Maestro generado exitosamente.")
        return analysis_result

    except Exception as e:
        print(f"  -> ❌ Analyzer: Error inesperado durante la generación del Índice Maestro: {e}")
        return None