import os
import requests 
import re

# --- CONFIGURAZIONE ---
REPO_OWNER = "BugbustersUnipd"
REPO_NAME = "DocumentazioneSWE"
MAIN_BRANCH = "main" 
INDEX_FILE_PATH = "index.html" # Il tuo index.html è nella root
# --- FINE CONFIGURAZIONE ---

def get_json_from_api(api_url):
    """Esegue una chiamata API a GitHub (pubblica, non serve token)."""
    try:
        response = requests.get(api_url)
        response.raise_for_status() 
        return response.json()
    except requests.RequestException as e:
        print(f"Errore API per {api_url}: {e}")
        return None

def update_index_file(placeholder_start, placeholder_end, html_content):
    """Legge index.html e sostituisce il placeholder (solo il primo)."""
    if not html_content:
        html_content = "<p>Nessun documento trovato.</p>" # Messaggio di default

    try:
        with open(INDEX_FILE_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        pattern = re.compile(f"({re.escape(placeholder_start)})(.*?)({re.escape(placeholder_end)})", re.DOTALL)
        replacement_block = f"\\1\n{html_content}\n            ", "", candidatura_html)

    # 2. Processa Capitolato
    capitolato_html = process_simple_folder_content("SCELTA CAPITOLATO")
    update_index_file("", "", capitolato_html)

    # 3. Processa Norme
    norme_html = process_simple_folder_content("NORME")
    update_index_file("", "", norme_html)

    # 4. Processa Verbali Interni
    interni_html = process_nested_folder("VERBALI/Interni", "Interni")
    update_index_file("", "", interni_html)

    # 5. Processa Verbali Esterni
    esterni_html = process_nested_folder("VERBALI/Esterni", "Esterni")
    update_index_file("", "", esterni_html)
    
    print("Sincronizzazione completata.")

if __name__ == "__main__":
    main()