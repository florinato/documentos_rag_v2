# extractor.py
import os

import docx  # Para archivos .docx
import pypdf  # Para archivos .pdf


def extract_text_from_pdf(file_path):
    """Extrae texto de un archivo PDF."""
    try:
        with open(file_path, 'rb') as file:
            reader = pypdf.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"Error al leer el PDF '{file_path}': {e}")
        return ""

def extract_text_from_docx(file_path):
    """Extrae texto de un archivo DOCX."""
    try:
        doc = docx.Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        print(f"Error al leer el DOCX '{file_path}': {e}")
        return ""

def extract_text_from_txt(file_path):
    """Lee texto de un archivo de texto plano (TXT)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error al leer el TXT '{file_path}': {e}")
        return ""

def extract_text_from_document(file_path):
    """
    Detecta la extensión del archivo y usa el extractor adecuado.
    Soporta .pdf, .docx, y .txt.

    Args:
        file_path (str): La ruta del archivo del que se desea extraer el texto.

    Returns:
        str: El texto extraído, o una cadena vacía si el formato no es compatible o hay un error.
    """
    # Obtener la extensión del archivo en minúsculas
    _, file_extension = os.path.splitext(file_path)
    file_extension = file_extension.lower()

    if file_extension == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_extension == '.docx':
        return extract_text_from_docx(file_path)
    elif file_extension == '.txt':
        return extract_text_from_txt(file_path)
    else:
        print(f"Error: El formato de archivo '{file_extension}' no es compatible.")
        print("Actualmente se soportan: .pdf, .docx, .txt")
        return ""