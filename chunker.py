# chunker.py
import re
from typing import List


def create_parent_chunks(text: str, parent_chunk_size: int = 8000, parent_chunk_overlap: int = 400) -> List[str]:
    """Crea chunks grandes (padres) con un tamaño y solapamiento fijos."""
    if not text:
        return []
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + parent_chunk_size
        chunks.append(text[start:end])
        start += parent_chunk_size - parent_chunk_overlap
    
    return chunks

def create_child_chunks(parent_chunk: str) -> List[str]:
    """
    Crea chunks pequeños (hijos) a partir de un chunk padre.
    Usa la lógica híbrida de párrafos/frases para mantener la coherencia semántica.
    """
    if not parent_chunk:
        return []

    # Intento de división por párrafos
    paragraphs = [p.strip() for p in parent_chunk.split('\n\n') if p.strip()]
    
    is_wall_of_text = len(paragraphs) < 5 and len(parent_chunk) > 1000

    if not is_wall_of_text and paragraphs:
        return paragraphs
    else:
        # Fallback a división por frases
        sentences = re.split(r'(?<=[.?!])\s+', parent_chunk)
        return [s.strip() for s in sentences if s.strip()]


if __name__ == "__main__":
    with open("documentos_para_rag/magia.txt", "r", encoding="utf-8") as f:
        sample_text = f.read()

    print("--- Probando RAG Jerárquico ---")
    
    # 1. Crear chunks padre
    parent_chunks = create_parent_chunks(sample_text)
    print(f"Documento dividido en {len(parent_chunks)} chunks PADRE.")

    # 2. Crear chunks hijo desde el primer padre
    if parent_chunks:
        child_chunks = create_child_chunks(parent_chunks[0])
        print(f"El primer chunk PADRE ha sido dividido en {len(child_chunks)} chunks HIJO.")
        print("\nEjemplo de un chunk HIJO:")
        print(f"'{child_chunks[0]}'")