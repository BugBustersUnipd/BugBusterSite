import os
import requests
import re
import pathlib
import urllib.parse
import json
import datetime
import time

# --- CONFIGURAZIONE ---
REPO_OWNER = "BugbustersUnipd"
REPO_NAME = "DocumentazioneSWE"
MAIN_BRANCH = "main" 
INDEX_FILE_PATH = "index.html" 
LOCAL_DOCS_DIR = "assets/docs"
METADATA_FILE = os.path.join(LOCAL_DOCS_DIR, '.sync_meta.json')
MAX_RETRIES = 3
RETRY_DELAY = 2  # secondi
# --- FINE CONFIGURAZIONE ---

def get_json_from_api(api_url, retries=MAX_RETRIES):
    """Esegue una chiamata API a GitHub con retry logic."""
    for attempt in range(retries):
        try:
            response = requests.get(api_url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Tentativo {attempt + 1}/{retries} fallito per {api_url}: {e}")
            if attempt < retries - 1:
                time.sleep(RETRY_DELAY)
            else:
                print(f"Errore definitivo API per {api_url}")
                return None
    return None


def load_meta():
    """Carica i metadata dal file JSON."""
    try:
        if os.path.exists(METADATA_FILE):
            with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Errore parsing metadata JSON: {e}")
    except Exception as e:
        print(f"Errore caricamento metadata: {e}")
    return {}


def save_meta(meta):
    """Salva i metadata nel file JSON."""
    try:
        pathlib.Path(LOCAL_DOCS_DIR).mkdir(parents=True, exist_ok=True)
        with open(METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Errore salvataggio metadata: {e}")


def update_index_file(placeholder_start, placeholder_end, html_content):
    """Sostituisce il blocco compreso tra placeholder_start e placeholder_end in INDEX_FILE_PATH."""
    if not html_content:
        html_content = "                <p>Nessun documento trovato.</p>"

    try:
        # Verifica che il file index.html esista
        if not os.path.exists(INDEX_FILE_PATH):
            print(f"ERRORE: File {INDEX_FILE_PATH} non trovato!")
            return

        with open(INDEX_FILE_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        pattern = re.compile(
            f"({re.escape(placeholder_start)})(.*?)({re.escape(placeholder_end)})", 
            re.DOTALL
        )

        if pattern.search(content) is None:
            print(f"ERRORE: Placeholder {placeholder_start} non trovato in {INDEX_FILE_PATH}.")
            return

        replacement_block = f"\\1\n{html_content}\n            \\3"
        new_content = pattern.sub(replacement_block, content, count=1)

        with open(INDEX_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"✓ Aggiornato {placeholder_start}")
    except Exception as e:
        print(f"Errore durante l'aggiornamento di {INDEX_FILE_PATH}: {e}")


def slugify(name):
    """Sanitizza il nome per uso in path."""
    s = re.sub(r"[^A-Za-z0-9.]+", '_', name)
    return s.strip('_')


def natural_key(name):
    """Genera una chiave per ordinamento naturale."""
    parts = re.findall(r"\d+|\D+", name)
    key = []
    for p in parts:
        if p.isdigit():
            key.append(int(p))
        else:
            key.append(p.lower())
    return key


def download_file(url, local_path, meta_key, file_sha, meta):
    """Scarica un file da URL e aggiorna i metadata."""
    try:
        r = requests.get(url, stream=True, timeout=30)
        r.raise_for_status()
        
        # Crea directory se non esiste
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        with open(local_path, 'wb') as out_f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    out_f.write(chunk)
        
        print(f"✓ Scaricato/aggiornato: {local_path}")
        meta[meta_key] = file_sha
        meta[meta_key + '::updated_at'] = datetime.datetime.utcnow().isoformat()
        return True
    except requests.RequestException as e:
        print(f"✗ Errore download {url}: {e}")
        return False


def process_simple_folder_content(folder_path, sort_desc=False):
    """Genera HTML per cartelle semplici (Candidatura, Capitolato, Norme)."""
    print(f"\n→ Processando cartella: {folder_path}")
    html_output = "                <ul>\n"
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{folder_path}?ref={MAIN_BRANCH}"
    
    files = get_json_from_api(api_url)
    if not files or not isinstance(files, list):
        print(f"  Nessun file trovato o errore API per {folder_path}")
        return "" 

    if sort_desc:
        try:
            files.sort(key=lambda f: natural_key(f.get('name', '')), reverse=True)
        except Exception:
            files.sort(key=lambda f: f.get('name', ''), reverse=True)

    found_files = False
    meta = load_meta()
    
    for file in files:
        if file.get('type') == 'file' and file.get('name', '').lower().endswith('.pdf'):
            pdf_url = file.get('download_url')
            pdf_name = file.get('name')
            file_sha = file.get('sha')

            safe_folder = slugify(folder_path)
            safe_name = slugify(pdf_name)
            local_dir = os.path.join(LOCAL_DOCS_DIR, safe_folder)
            local_path = os.path.join(local_dir, safe_name)

            meta_key = '/'.join([folder_path, pdf_name])
            need_download = True
            
            if os.path.exists(local_path) and meta.get(meta_key) == file_sha:
                need_download = False
                print(f"  - {pdf_name} (già aggiornato)")

            if need_download:
                if not download_file(pdf_url, local_path, meta_key, file_sha, meta):
                    continue

            rel_path = '/'.join([
                LOCAL_DOCS_DIR.replace('\\', '/'), 
                urllib.parse.quote(safe_folder), 
                urllib.parse.quote(safe_name)
            ])

            html_output += f"""                    <li>
                        <a href="{rel_path}" target="_blank" rel="noopener noreferrer">
                            <span class="file-icon">📄</span> {pdf_name}
                        </a>
                    </li>
"""
            found_files = True
    
    save_meta(meta)
    html_output += "                </ul>"
    return html_output if found_files else ""


def process_nested_folder(folder_path, type_name):
    """Genera HTML per cartelle complesse (Verbali)."""
    print(f"\n→ Processando cartella nidificata: {folder_path}")
    html_output = ""
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{folder_path}?ref={MAIN_BRANCH}"
    
    folders = get_json_from_api(api_url)
    if not folders or not isinstance(folders, list):
        print(f"  Nessuna cartella trovata o errore API per {folder_path}")
        return ""

    folders.sort(key=lambda x: x.get('name', ''))
    meta = load_meta()

    for folder in folders:
        if folder.get('type') == 'dir':
            folder_name = folder.get('name')
            folder_api_url = folder.get('url')

            print(f"  → Subfolder: {folder_name}")
            files = get_json_from_api(folder_api_url)
            if not files or not isinstance(files, list):
                continue

            pdf_link = None
            pdf_name = None
            file_sha = None
            
            for file in files:
                if file.get('type') == 'file' and file.get('name', '').lower().endswith('.pdf'):
                    pdf_link = file.get('download_url')
                    pdf_name = file.get('name')
                    file_sha = file.get('sha')
                    break

            if pdf_link and pdf_name:
                # Formattazione nome display
                display_name = folder_name.replace(' ', '_')
                
                # Mappatura specifica per verbali esterni
                verbali_map = {
                    "VE 24-10-2025 [M31]": "VE_24-10-2025 [M31]",
                    "VE 22 10 2025 [Miriade]": "VE_22-10-2025 [Miriade]",
                    "VE 24-10-25[EggOn]": "VE_24-10-25 [EggOn]"
                }
                display_name = verbali_map.get(folder_name, display_name)

                data_folder_id = f"verbale-{type_name.lower()}-{re.sub(r'[^a-z0-9]+', '-', folder_name.lower())}"

                safe_folder = slugify(folder_path)
                safe_folder_name = slugify(folder_name)
                safe_name = slugify(pdf_name)

                local_dir = os.path.join(LOCAL_DOCS_DIR, safe_folder, safe_folder_name)
                local_path = os.path.join(local_dir, safe_name)

                meta_key = '/'.join([folder_path, folder_name, pdf_name])
                need_download = True
                
                if os.path.exists(local_path) and meta.get(meta_key) == file_sha:
                    need_download = False
                    print(f"    - {pdf_name} (già aggiornato)")

                if need_download:
                    if not download_file(pdf_link, local_path, meta_key, file_sha, meta):
                        continue

                rel_path = '/'.join([
                    LOCAL_DOCS_DIR.replace('\\', '/'), 
                    urllib.parse.quote(safe_folder), 
                    urllib.parse.quote(safe_folder_name), 
                    urllib.parse.quote(safe_name)
                ])

                html_output += f"""                    <div class="subfolder">
                        <div class="folder-header" data-folder="{data_folder_id}">
                            <h4><span class="folder-icon">📁</span> {display_name}</h4>
                            <span class="toggle-icon">+</span>
                        </div>
                        <div class="folder-content" id="{data_folder_id}-content">
                            <ul>
                                <li>
                                    <a href="{rel_path}" target="_blank" rel="noopener noreferrer">
                                        <span class="file-icon">📄</span> {pdf_name}
                                    </a>
                                </li>
                            </ul>
                        </div>
                    </div>
"""
    
    save_meta(meta)
    return html_output


def main():
    print("=" * 60)
    print("Avvio sincronizzazione documenti da GitHub...")
    print("=" * 60)
    
    try:
        # 1. Candidatura
        candidatura_html = process_simple_folder_content("CANDIDATURA PROGETTO")
        update_index_file("<!-- START_CANDIDATURA -->", "<!-- END_CANDIDATURA -->", candidatura_html)

        # 2. Capitolato
        capitolato_html = process_simple_folder_content("SCELTA CAPITOLATO")
        update_index_file("<!-- START_CAPITOLATO -->", "<!-- END_CAPITOLATO -->", capitolato_html)

        # 3. Norme
        norme_html = process_simple_folder_content("NORME DI PROGETTO")
        update_index_file("<!-- START_NORME -->", "<!-- END_NORME -->", norme_html)

        # 4. Diario di bordo
        diario_html = process_simple_folder_content("DIARIO DI BORDO")
        update_index_file("<!-- START_DIARIO -->", "<!-- END_DIARIO -->", diario_html)

        # 5. Dichiarazione impegni
        dichiarazione_html = process_simple_folder_content("DICHIARAZIONE IMPEGNI")
        update_index_file("<!-- START_DICHIARAZIONE -->", "<!-- END_DICHIARAZIONE -->", dichiarazione_html)

        # 6. Glossario
        glossario_html = process_simple_folder_content("GLOSSARIO")
        update_index_file("<!-- START_GLOSSARIO -->", "<!-- END_GLOSSARIO -->", glossario_html)

        # 7. Verbali Interni
        interni_html = process_nested_folder("VERBALI/Interni", "Interni")
        update_index_file("<!-- START_VERBALI_INTERNI -->", "<!-- END_VERBALI_INTERNI -->", interni_html)

        # 8. Verbali Esterni
        esterni_html = process_nested_folder("VERBALI/Esterni", "Esterni")
        update_index_file("<!-- START_VERBALI_ESTERNI -->", "<!-- END_VERBALI_ESTERNI -->", esterni_html)
        
        print("\n" + "=" * 60)
        print("✓ Sincronizzazione completata con successo!")
        print("=" * 60)
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"✗ ERRORE durante la sincronizzazione: {e}")
        print("=" * 60)
        raise


if __name__ == "__main__":
    main()
