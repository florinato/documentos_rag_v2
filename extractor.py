# extractor.py (Versión Página por Página)
import os

import docx
import pypdf


def extract_text_from_pdf_paginated(file_path: str) -> list[str]:
    """Extrae texto de un archivo PDF, devolviendo una lista de strings, una por página."""
    pages_text = []
    try:
        with open(file_path, 'rb') as file:
            reader = pypdf.PdfReader(file)
            for page in reader.pages:
                text = page.extract_text()
                if text:  # Solo añadir páginas que contienen texto
                    pages_text.append(text)
        print(f"  -> PDF procesado. {len(pages_text)} páginas con texto extraído.")
        return pages_text
    except Exception as e:
        print(f"  -> ⚠️ Error al leer el PDF '{file_path}': {e}")
        return []

def extract_text_from_docx(file_path: str) -> str:
    """Extrae texto de un archivo DOCX como un solo bloque."""
    try:
        doc = docx.Document(file_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
    except Exception as e:
        print(f"  -> ⚠️ Error al leer el DOCX '{file_path}': {e}")
        return ""

def extract_text_from_txt(file_path: str) -> str:
    """Lee texto de un archivo TXT como un solo bloque."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"  -> ⚠️ Error al leer el TXT '{file_path}': {e}")
        return ""

# Función principal unificada
def extract_text_from_document(file_path):
    """
    Detecta la extensión y usa el extractor adecuado.
    Para PDFs, devuelve una lista de páginas. Para otros, un solo string.
    """
    _, file_extension = os.path.splitext(file_path.lower())

    if file_extension == '.pdf':
        return extract_text_from_pdf_paginated(file_path)
    elif file_extension == '.docx':
        return extract_text_from_docx(file_path)
    elif file_extension == '.txt':
        return extract_text_from_txt(file_path)
    else:
        print(f"  -> ❌ Error: Formato '{file_extension}' no compatible.")
        return None