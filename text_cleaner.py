# text_cleaner.py
import re


def clean_and_normalize_text(text: str) -> str:
    """
    Realiza una limpieza básica y normalización del texto extraído.
    """
    if not text:
        return ""

    # 1. Reemplazar múltiples saltos de línea con un máximo de dos (para párrafos)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    # 2. Eliminar espacios o tabulaciones al principio y final de cada línea
    lines = text.split('\n')
    cleaned_lines = [line.strip() for line in lines]
    text = '\n'.join(cleaned_lines)

    # 3. Reemplazar múltiples espacios con uno solo
    text = re.sub(r' +', ' ', text)
    
    # Puedes añadir más reglas de limpieza aquí si descubres patrones no deseados
    # Por ejemplo, eliminar encabezados/pies de página si siguen un patrón predecible.

    print("  -> Texto bruto limpiado y normalizado.")
    return text.strip()