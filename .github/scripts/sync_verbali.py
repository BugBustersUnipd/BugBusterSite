import os
import requests 
import re

# --- CONFIGURAZIONE ---
REPO_OWNER = "BugbustersUnipd"
REPO_NAME = "DocumentazioneSWE"
MAIN_BRANCH = "main" 
INDEX_FILE_PATH = "index.html" 
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
    """Sostituisce il blocco compreso tra placeholder_start e placeholder_end in INDEX_FILE_PATH.

    placeholder_start e placeholder_end devono essere stringhe esatte presenti in `index.html`,
    ad esempio <!-- START_NORME --> e <!-- END_NORME -->.
    """
    if not html_content:
        html_content = "<p>Nessun documento trovato.</p>"

    try:
        with open(INDEX_FILE_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        pattern = re.compile(f"({re.escape(placeholder_start)})(.*?)({re.escape(placeholder_end)})", re.DOTALL)

        if pattern.search(content) is None:
            print(f"ERRORE: Placeholder {placeholder_start} non trovato in {INDEX_FILE_PATH}.")
            return

        replacement_block = f"\\1\n{html_content}\n            \\3"

        # Sostituisce solo la prima occorrenza
        new_content = pattern.sub(replacement_block, content, count=1)

        with open(INDEX_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Aggiornato {placeholder_start}")
    except Exception as e:
        print(f"Errore durante l'aggiornamento di {INDEX_FILE_PATH}: {e}")

def process_simple_folder_content(folder_path):
    """Genera HTML per cartelle semplici (Candidatura, Capitolato, Norme)."""
    html_output = "<ul>"
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{folder_path}?ref={MAIN_BRANCH}"
    
    files = get_json_from_api(api_url)
    if not files or not isinstance(files, list):
        print(f"Nessun file trovato o errore API per {folder_path}")
        return "" 

    found_files = False
    for file in files:
        if file.get('type') == 'file' and file.get('name', '').lower().endswith('.pdf'):
            pdf_link = file.get('download_url') 
            pdf_name = file.get('name')
            html_output += f"""
                        <li>
                            <a href="{pdf_link}" target="_blank" rel="noopener noreferrer">
                                <span class="file-icon">📄</span> {pdf_name}
                            </a>
                        </li>
"""
            found_files = True
    
    html_output += "</ul>"
    return html_output if found_files else ""

def process_nested_folder(folder_path, type_name):
    """Genera HTML per cartelle complesse (Verbali)."""
    html_output = ""
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{folder_path}?ref={MAIN_BRANCH}"
    
    folders = get_json_from_api(api_url)
    if not folders or not isinstance(folders, list):
        print(f"Nessuna cartella trovata o errore API per {folder_path}")
        return ""

    folders.sort(key=lambda x: x.get('name')) 

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
                                        <a href="{pdf_link}" target="_blank" rel="noopener noreferrer">
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
    update_index_file("<!-- START_CANDIDATURA -->", "<!-- END_CANDIDATURA -->", candidatura_html)

    # 2. Processa Capitolato
    capitolato_html = process_simple_folder_content("SCELTA CAPITOLATO")
    update_index_file("<!-- START_CAPITOLATO -->", "<!-- END_CAPITOLATO -->", capitolato_html)

    # 3. Processa Norme (cartella corretta: NORME DI PROGETTO)
    norme_html = process_simple_folder_content("NORME DI PROGETTO")
    update_index_file("<!-- START_NORME -->", "<!-- END_NORME -->", norme_html)

    # 4. Processa Verbali Interni
    interni_html = process_nested_folder("VERBALI/Interni", "Interni")
    update_index_file("<!-- START_VERBALI_INTERNI -->", "<!-- END_VERBALI_INTERNI -->", interni_html)

    # 5. Processa Verbali Esterni
    esterni_html = process_nested_folder("VERBALI/Esterni", "Esterni")
    update_index_file("<!-- START_VERBALI_ESTERNI -->", "<!-- END_VERBALI_ESTERNI -->", esterni_html)
    
    print("Sincronizzazione completata.")

if __name__ == "__main__":
    main()