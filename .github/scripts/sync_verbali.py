import os
import shutil
import re

# --- CONFIGURAZIONE ---
SOURCE_REPO_PATH = "private_docs_repo"
WEBSITE_DOCS_PATH = "docs"
INDEX_FILE_PATH = os.path.join(WEBSITE_DOCS_PATH, "index.html")
TARGET_ASSETS_DIR = os.path.join(WEBSITE_DOCS_PATH, "verbali_autogen")
# --- FINE CONFIGURAZIONE ---

def update_index_file(placeholder_start, placeholder_end, html_content):
    """
    Legge index.html e sostituisce il placeholder con il nuovo HTML.
    USA count=1 PER PREVENIRE DUPLICAZIONI.
    """
    if not html_content:
        html_content = "<p>Nessun verbale trovato.</p>"

    try:
        with open(INDEX_FILE_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        # Regex per trovare il blocco
        pattern = re.compile(f"({re.escape(placeholder_start)})(.*?)({re.escape(placeholder_end)})", re.DOTALL)
        
        # Costruisci il blocco sostitutivo
        replacement_block = f"\\1\n{html_content}\n                        \\3"

        if pattern.search(content) is None:
            print(f"ERRORE: Placeholder {placeholder_start} non trovato in {INDEX_FILE_PATH}. Non aggiorno nulla.")
            return

        # ==========================================================
        # ECCO LA MODIFICA CHIAVE: count=1
        # Sostituisce solo la *prima* occorrenza trovata.
        new_content = pattern.sub(replacement_block, content, count=1)
        # ==========================================================

        # Controllo di sicurezza: avvisa se trova altri placeholder
        if pattern.search(new_content):
             print(f"ATTENZIONE: Trovati placeholder duplicati per {placeholder_start} in index.html. "
                   f"Sostituito solo il primo. Il file index.html va pulito manualmente.")

        with open(INDEX_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Aggiornato {placeholder_start} in {INDEX_FILE_PATH} (sostituito 1 blocco)")
    
    except Exception as e:
        print(f"Errore durante l'aggiornamento di {INDEX_FILE_PATH}: {e}")

def process_verbali(source_path, type_name):
    """
    Copia le cartelle dei verbali e genera l'HTML.
    """
    html_output = ""
    
    if not os.path.exists(source_path):
        print(f"Cartella sorgente non trovata: {source_path}")
        return ""

    # Ordina le cartelle per nome, così appaiono in ordine
    try:
        folder_list = sorted(os.listdir(source_path))
    except Exception:
        folder_list = []

    for folder_name in folder_list:
        source_folder_path = os.path.join(source_path, folder_name)
        
        if os.path.isdir(source_folder_path):
            try:
                # 1. Copia l'intera cartella
                target_folder_path = os.path.join(TARGET_ASSETS_DIR, type_name, folder_name)
                # copytree fallisce se la cartella esiste già, la rimuoviamo prima per sicurezza
                if os.path.exists(target_folder_path):
                    shutil.rmtree(target_folder_path)
                shutil.copytree(source_folder_path, target_folder_path)

                # 2. Trova il PDF
                pdf_name = None
                for file in os.listdir(target_folder_path):
                    if file.lower().endswith(".pdf"):
                        pdf_name = file
                        break
                
                if not pdf_name:
                    print(f"Nessun PDF trovato in {target_folder_path}")
                    continue

                # 3. Costruisci il link RELATIVO
                link_href = f"verbali_autogen/{type_name}/{folder_name}/{pdf_name}"
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
                                        <a href="{link_href}" target="_blank">
                                            <span class="file-icon">📄</span> {pdf_name}
                                        </a>
                                    </li>
                                </ul>
                            </div>
                        </div>
"""
            except Exception as e:
                print(f"Errore processando {source_folder_path}: {e}")
                
    return html_output

def main():
    # Pulisci e ricrea la cartella di destinazione dei PDF
    if os.path.exists(TARGET_ASSETS_DIR):
        shutil.rmtree(TARGET_ASSETS_DIR)
    os.makedirs(TARGET_ASSETS_DIR, exist_ok=True)
    
    # Processa Verbali Interni
    print("Processo Verbali Interni...")
    source_interni = os.path.join(SOURCE_REPO_PATH, "VERBALI", "Interni")
    interni_html = process_verbali(source_interni, "Interni")
    update_index_file("", "", interni_html)

    # Processa Verbali Esterni
    print("Processo Verbali Esterni...")
    source_esterni = os.path.join(SOURCE_REPO_PATH, "VERBALI", "Esterni")
    esterni_html = process_verbali(source_esterni, "Esterni")
    update_index_file("", "", esterni_html)

if __name__ == "__main__":
    main()