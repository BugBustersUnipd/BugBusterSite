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
        
        # --- QUESTA È LA LINEA CORRETTA ---
        # Sostituisce il contenuto tra il gruppo 1 (\1) e il gruppo 3 (\3)
        replacement_block = f"\\1\n{html_content}\n            \\3"
        # --- FINE DELLA CORREZIONE ---

        if pattern.search(content) is None:
            print(f"ERRORE: Placeholder {placeholder_start} non trovato in {INDEX_FILE_PATH}.")
            return

        # Sostituisce solo la *prima* occorrenza per prevenire duplicati
        new_content = pattern.sub(replacement_block, content, count=1)

        with open(INDEX_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Aggiornato {placeholder_start}")
    
    except Exception as e:
        print(f"Errore durante l'aggiornamento di {INDEX_FILE_PATH}: {e}")

def process_simple_folder_content(folder_path):
    """
    Genera HTML per cartelle semplici (Candidatura, Capitolato, Norme)
    che contengono direttamente i PDF.
    """
    html_output = "<ul>"
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{folder_path}?ref={MAIN_BRANCH}"
    
    files = get_json_from_api(api_url)
    if not files or not isinstance(files, list):
        print(f"Nessun file trovato o errore API per {folder_path}")
        return "" 

    found_files = False
    for file in files:
        if file.get('type') == 'file' and file.get('name', '').lower().endswith('.pdf'):
            pdf_link = file.get('download_url') # Link diretto al PDF
            pdf_name = file.get('name')
            html_output += f"""
                        <li>
                            <a href="{pdf_link}" target="_blank">
                                <span class="file-icon">📄</span> {pdf_name}
                            </a>
                        </li>
"""
            found_files = True
    
    html_output += "</ul>"
    return html_output if found_files else ""

def process_nested_folder(folder_path, type_name):
    """
    Genera HTML per cartelle complesse (Verbali)
    che contengono altre cartelle.
    """
    html_output = ""
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{folder_path}?ref={MAIN_BRANCH}"
    
    folders = get_json_from_api(api_url)
    if not folders or not isinstance(folders, list):
        print(f"Nessuna cartella trovata o errore API per {folder_path}")
        return ""

    folders.sort(key=lambda x: x.get('name')) # Ordina per nome

    for folder in folders:
        if folder.get('type') == 'dir':
            folder_name = folder.get('name')
            folder_api_url = folder.get('url')
            
            files = get_json_from_api(folder_api_url)
            if not files or not isinstance(files, list):
                continue

            pdf_link = None
            pdf_name = None
            for file in files:
                if file.get('type') == 'file' and file.get('name', '').lower().endswith('.pdf'):
                    pdf_link = file.get('download_url') 
                    pdf_name = file.get('name')
                    break 
            
            if pdf_link:
                data_folder_id = f"verbale-{type_name.lower()}-{re.sub(r'[^a-z0-9]+', '-', folder_name.lower())}"

                html_output += f"""
                        <div class="subfolder">
                            <div class="folder-header" data-folder="{data_folder_id}">
                                <h4><span class="folder-icon">📁</span> {folder_name}</h4>
                                <span class="toggle-icon">+</span>
                            </div>
                            <div class="folder-content" id="{data_folder_id}-content">
                                <ul>
                                    <li>
                                        <a href="{pdf_link}" target="_blank">
                                            <span class="file-icon">📄</span> {pdf_name}
                                        </a>
                                    </li>
                                </ul>
                            </div>
                        </div>
"""
    return html_output

def main():
    print("Avvio sincronizzazione documenti...")

    # 1. Processa Candidatura
    candidatura_html = process_simple_folder_content("CANDIDATURA PROGETTO")
    update_index_file("", "", candidatura_html)

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