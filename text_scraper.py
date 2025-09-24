# text_scraper.py
import requests
import trafilatura

# Ya no necesitamos requests_html, lo que simplifica las cosas

def extract_text_from_url(url: str) -> str:
    """
    Extrae el texto principal de una URL usando el método más robusto primero.
    Trata todas las URLs como potenciales páginas web y usa 'trafilatura' para 
    encontrar y limpiar el contenido principal.
    """
    print(f"  -> Extrayendo contenido de: {url}")

    try:
        # 1. Descargar el contenido HTML de la URL de forma segura.
        # Usamos un user-agent para parecer un navegador normal.
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        downloaded_html = response.text

        if not downloaded_html:
            print("    -> Fallo: La URL no devolvió contenido.")
            return ""

        # 2. Usar 'trafilatura' para analizar el HTML y extraer el texto principal.
        # Esta es la función clave que elimina menús, anuncios, código, etc.
        main_text = trafilatura.extract(
            downloaded_html,
            include_comments=False,
            include_tables=False,
            no_fallback=True  # No queremos que devuelva el body si no encuentra nada
        )

        if main_text and len(main_text) > 100: # Nos aseguramos de que haya extraído algo sustancial
            print("    -> ¡Éxito! Contenido principal extraído y limpiado por 'trafilatura'.")
            return main_text
        else:
            print("    -> ADVERTENCIA: 'trafilatura' no encontró un cuerpo de texto principal claro. El documento podría estar vacío o tener un formato inusual.")
            # Como último recurso, devolvemos el texto plano del body si existe, aunque puede estar sucio.
            # Esto es mejor que nada, pero no ideal.
            return trafilatura.extract(downloaded_html)

    except requests.RequestException as e:
        print(f"    -> ERROR: No se pudo descargar la URL. {e}")
        return ""
    except Exception as e:
        print(f"    -> ERROR: Ocurrió un error inesperado durante el scraping. {e}")
        return ""