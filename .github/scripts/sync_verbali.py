import os
import requests
import re

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("DOCS_PAT")
REPO_OWNER = "BugbustersUnipd"
REPO_NAME = "DocumentazioneSWE"
INDEX_FILE = "index.html"
# --------------------

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def get_folders(api_url):
    """Prende la lista di cartelle da un URL API di GitHub."""
    response = requests.get(api_url, headers=HEADERS)
    response.raise_for_status() # Lancia un errore se la richiesta fallisce
    items = response.json()
    # Filtra solo per le cartelle (type 'dir')
    return [item for item in items if item.get("type") == "dir"]

def get_pdf_in_folder(folder_item):
    """Cerca un PDF dentro una cartella e restituisce nome e link."""
    folder_url = folder_item.get("url")
    if not folder_url:
        return None, None
        
    response = requests.get(folder_url, headers=HEADERS)
    response.raise_for_status()
    files = response.json()
    
    for file in files:
        if file.get("type") == "file" and file.get("name", "").endswith(".pdf"):
            # Trovato! Restituiamo il link alla pagina web del file e il nome
            return file.get("html_url"), file.get("name")
            
    return None, None

def build_html_for_folders(folders):
    """Costruisce il blocco HTML per la lista di cartelle e PDF."""
    html_output = ""
    if not folders:
        return None # Non modifichiamo nulla se non troviamo cartelle

    for folder in folders:
        folder_name = folder.get("name")
        pdf_link, pdf_name = get_pdf_in_folder(folder)
        
        if not pdf_link or not pdf_name:
            continue # Salta questa cartella se non c'è un PDF omonimo

        # Crea un ID unico per il JS, es. "verbale-20-10-2024"
        data_folder_id = f"verbale-{re.sub(r'[^a-z0-9]+', '-', folder_name.lower())}"

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

def update_index_file(placeholder_start, placeholder_end, html_content):
    """Legge index.html e sostituisce il placeholder con il nuovo HTML."""
    if html_content is None:
        print(f"Nessun contenuto da aggiornare per {placeholder_start}, lascio il placeholder di default.")
        return

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Regex per trovare il contenuto TRA i placeholder
    pattern = re.compile(f"({re.escape(placeholder_start)})(.*?)({re.escape(placeholder_end)})", re.DOTALL)
    
    # Sostituisce il contenuto, mantenendo i placeholder
    new_content = pattern.sub(f"\\1\n{html_content}\n                        \\3", content)

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Aggiornato {placeholder_start} in {INDEX_FILE}")


def main():
    if not TOKEN:
        print("Errore: Token DOCS_PAT non trovato. Assicurati sia nei Secrets.")
        return

    # --- Processa Verbali Interni ---
    print("Processo Verbali Interni...")
    api_interni_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/VERBALI/Interni"
    try:
        interni_folders = get_folders(api_interni_url)
        interni_html = build_html_for_folders(interni_folders)
        update_index_file("", "", interni_html)
    except Exception as e:
        print(f"Errore processando verbali interni: {e}")

    # --- Processa Verbali Esterni ---
    print("Processo Verbali Esterni...")
    api_esterni_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/VERBALI/Esterni"
    try:
        esterni_folders = get_folders(api_esterni_url)
        esterni_html = build_html_for_folders(esterni_folders)
        update_index_file("", "", esterni_html)
    except Exception as e:
        print(f"Errore processando verbali esterni: {e}")

if __name__ == "__main__":
    main()