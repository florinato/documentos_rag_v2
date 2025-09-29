# Asistente de Investigación RAG v2

Este proyecto es una aplicación de escritorio avanzada que implementa un sistema de Recuperación Aumentada por Generación (RAG). Te permite construir una base de conocimiento personal y conversacional a partir de diversas fuentes, como documentos locales y páginas web.

El sistema no solo almacena tus documentos, sino que los "entiende", catalogándolos y procesándolos a través de un pipeline de IA para permitir consultas profundas y respuestas contextualmente ricas.

## Explicación del Proyecto
El Asistente de Investigación RAG se construye sobre un pipeline de procesamiento y consulta de vanguardia, diseñado para maximizar la calidad del contexto y la precisión de las respuestas. La arquitectura, denominada "Rolls-Royce", se divide en dos fases principales: una ingesta de conocimiento inteligente y una consulta de múltiples etapas.
Cómo Funciona: El Pipeline de Ingesta
Cuando se añade un nuevo documento, no se almacena simplemente. Pasa por un sofisticado proceso de catalogación y estructuración:
Extracción y Limpieza: El sistema extrae el texto bruto de la fuente (archivo local o URL) y lo somete a un proceso de normalización para eliminar artefactos y prepararlo para el análisis.
Generación del Índice Maestro: El texto limpio se envía a un LLM que actúa como un "Editor Senior". Aprovechando una gran ventana de contexto, la IA analiza el documento de forma holística para crear un Índice Maestro. Este índice es un archivo de metadatos detallado que contiene:
Datos Bibliográficos: Título, autor y fecha de publicación.
Resumen Global: Una síntesis del propósito y contenido del documento.
Índice Estructurado: Una tabla de contenidos generada por IA, con un resumen de una frase para cada capítulo o sección.
Tags y Temas Fundamentales: Las palabras y conceptos clave del documento.
Chunking por Páginas y Embedding: El documento se divide en fragmentos del tamaño de una página. Cada uno de estos fragmentos se convierte en un vector numérico (embedding) y se almacena en una base de datos vectorial local, listo para la búsqueda semántica.
Cómo Funciona: El Pipeline de Consulta
Cuando un usuario hace una pregunta, el sistema inicia un proceso de razonamiento de varias etapas:
Traducción de Consulta Asistida por IA: La pregunta del usuario no se envía directamente a la base de datos. Primero, se le presenta a un LLM junto con el Índice Maestro del documento seleccionado y el historial de la conversación.
Plan de Búsqueda Híbrido: La IA, actuando como un investigador experto, utiliza este contexto para crear un plan de búsqueda. Este plan incluye:
Consultas Semánticas Optimizadas: Reescribe la pregunta del usuario para que sea conceptualmente más precisa.
Palabras Clave Esenciales: Extrae los términos específicos más importantes para anclar la búsqueda.
Búsqueda de Alta Precisión: El sistema combina las consultas semánticas y las palabras clave para realizar una búsqueda híbrida en la base de datos vectorial, recuperando los fragmentos (páginas) más relevantes del documento.
Síntesis de Respuesta Contextualizada: Finalmente, la IA recibe un "paquete de contexto" completo: la pregunta original del usuario, el prompt de la personalidad seleccionada, el historial de la conversación, el Índice Maestro del libro y los fragmentos recuperados. Con toda esta información, redacta una respuesta coherente, precisa y profundamente informada.
Características Clave
Ingesta Multi-Fuente: Añade conocimiento desde archivos locales (.pdf, .docx, .txt) o directamente desde URLs.
Índice Maestro por IA: Cada documento es automáticamente analizado y catalogado con un resumen, tags, y una tabla de contenidos estructurada.
Búsqueda Híbrida Inteligente: Combina la búsqueda semántica conceptual con la precisión de las palabras clave para encontrar la información más relevante.
Memoria Conversacional: El asistente recuerda el contexto de la conversación para responder a preguntas de seguimiento de forma natural.
Personalidades de IA Configurables: Crea y guarda diferentes "personalidades" (system prompts) para adaptar el tono y la tarea del asistente, convirtiéndolo en un consultor, un redactor o cualquier otro rol que necesites.
Interfaz de Escritorio Nativa: Construido con Flet para una experiencia de usuario rápida y fluida.
100% Privado y Local: Todos tus documentos y bases de conocimiento se almacenan de forma segura en tu propio ordenador.

## Vistazo a la Aplicación

(Aquí es donde colocarás tus capturas de pantalla)

*   **Pestaña de Consulta**: La interfaz principal de chat donde interactúas con tus documentos.
    ![IMAGEN DE LA PESTAÑA DE CONSULTA AQUÍ](capturas/consulta.png)
*   **Pestaña de Biblioteca**: Tu colección de conocimiento catalogada, mostrando los datos bibliográficos extraídos por la IA.
    ![IMAGEN DE LA PESTAÑA DE BIBLIOTECA AQUÍ](capturas/biblioteca.png)
*   **Pestaña de Personalidades**: El editor donde puedes crear y modificar los prompts que definen el comportamiento de tu asistente.
    ![IMAGEN DE LA PESTAÑA DE PERSONALIDADES AQUÍ](capturas/personalidad.png)

## Instalación

Sigue estos pasos para configurar y ejecutar el proyecto en tu entorno local.

### Requisitos

Asegúrate de tener instalado lo siguiente:

*   Python 3.9 o superior
*   pip (gestor de paquetes de Python)

### Pasos de Instalación

1.  **Clonar el repositorio**:
    ```bash
    git clone https://github.com/florinato/documentos_rag_v2.git
    cd documentos_rag_v2
    ```
2.  **Crear un entorno virtual (recomendado)**:
    ```bash
    python -m venv env_python
    ```
3.  **Activar el entorno virtual**:
    *   **Windows**:
        ```powershell
        .\env_python\Scripts\activate
        ```
    *   **macOS/Linux**:
        ```bash
        source env_python/bin/activate
        ```
4.  **Instalar las dependencias**:
    ```bash
    pip install -r requirements.txt
    ```
5.  **Configurar variables de entorno**:
    *   Busca el archivo `.env.example` en la raíz del proyecto.
    *   Crea una copia y renómbrala a `.env`.
    *   Abre el archivo `.env` y añade tu clave API de Google Gemini.
    ```dotenv
    GEMINI_API_KEY="TU_CLAVE_API_DE_GEMINI"
    ```

## Uso

Una vez que la instalación y configuración estén completas, puedes ejecutar la aplicación.

1.  Asegúrate de que tu entorno virtual esté activado.
2.  Ejecuta el siguiente comando en la terminal:
    ```bash
    flet run main_flet_app.py
