import os
import requests
import re
import pathlib
import urllib.parse
import json
import datetime

# --- CONFIGURAZIONE ---
REPO_OWNER = "BugbustersUnipd"
REPO_NAME = "DocumentazioneSWE"
MAIN_BRANCH = "main" 
INDEX_FILE_PATH = "index.html" 
LOCAL_DOCS_DIR = "assets/docs"
METADATA_FILE = os.path.join(LOCAL_DOCS_DIR, '.sync_meta.json')
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


def load_meta():
    try:
        if os.path.exists(METADATA_FILE):
            with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_meta(meta):
    try:
        pathlib.Path(LOCAL_DOCS_DIR).mkdir(parents=True, exist_ok=True)
        with open(METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Errore salvataggio metadata: {e}")

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
    meta = load_meta()
    for file in files:
        if file.get('type') == 'file' and file.get('name', '').lower().endswith('.pdf'):
            pdf_url = file.get('download_url')
            pdf_name = file.get('name')
            file_sha = file.get('sha')

            # salva il PDF sotto assets/docs/<sanitized_folder>/<sanitized_name>
            def slugify(name):
                # sostituisce spazi e caratteri non alfanumerici con underscore
                s = re.sub(r"[^A-Za-z0-9.]+", '_', name)
                return s.strip('_')

            safe_folder = slugify(folder_path)
            safe_name = slugify(pdf_name)
            local_dir = os.path.join(LOCAL_DOCS_DIR, safe_folder)
            pathlib.Path(local_dir).mkdir(parents=True, exist_ok=True)
            local_path = os.path.join(local_dir, safe_name)

            # Scarica o aggiorna il file se la sha remota è cambiata
            meta_key = '/'.join([folder_path, pdf_name])
            need_download = True
            if os.path.exists(local_path) and meta.get(meta_key) == file_sha:
                need_download = False

            if need_download:
                try:
                    r = requests.get(pdf_url, stream=True)
                    r.raise_for_status()
                    with open(local_path, 'wb') as out_f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                out_f.write(chunk)
                    print(f"Scaricato/aggiornato: {local_path}")
                    meta[meta_key] = file_sha
                    # salva timestamp di aggiornamento
                    try:
                        meta[meta_key + '::updated_at'] = datetime.datetime.utcnow().isoformat()
                    except Exception:
                        meta[meta_key + '::updated_at'] = ''
                except requests.RequestException as e:
                    print(f"Errore download {pdf_url}: {e}")
                    continue

            # href relativo per aprire nel viewer del browser (index.html è nella root)
            rel_path = '/'.join([LOCAL_DOCS_DIR.replace('\\', '/'), urllib.parse.quote(safe_folder), urllib.parse.quote(safe_name)])

            html_output += f"""
                        <li>
                            <a href="{rel_path}" target="_blank" rel="noopener noreferrer">
                                <span class=\"file-icon\">📄</span> {pdf_name}
                            </a>
                        </li>
"""
        found_files = True
    # save metadata after processing folder
    save_meta(meta)
    # compute last updated timestamp for this folder (if available)
    last_times = []
    for k in meta.keys():
        if k.startswith(folder_path + '/'):
            t = meta.get(k + '::updated_at')
            if t:
                last_times.append(t)

    if last_times:
        try:
            last_iso = max(last_times)
            last_dt = datetime.datetime.fromisoformat(last_iso)
            # format in modo leggibile
            last_str = last_dt.strftime('%d %b %Y %H:%M UTC')
            # prepend a small notice
            html_output = f'<p class="last-updated">Ultimo aggiornamento: {last_str}</p>\n' + html_output
        except Exception:
            pass

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

    meta = load_meta()
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
                    file_sha = file.get('sha')
                    break

            if pdf_link and pdf_name:
                # crea id per aria/JS
                data_folder_id = f"verbale-{type_name.lower()}-{re.sub(r'[^a-z0-9]+', '-', folder_name.lower())}"

                # salva localmente in una struttura sanificata
                def slugify(name):
                    return re.sub(r"[^A-Za-z0-9.]+", '_', name).strip('_')

                safe_folder = slugify(folder_path)
                safe_folder_name = slugify(folder_name)
                safe_name = slugify(pdf_name)

                local_dir = os.path.join(LOCAL_DOCS_DIR, safe_folder, safe_folder_name)
                pathlib.Path(local_dir).mkdir(parents=True, exist_ok=True)
                local_path = os.path.join(local_dir, safe_name)

                # decide se scaricare o aggiornare basandosi sulla sha
                meta = load_meta()
                meta_key = '/'.join([folder_path, folder_name, pdf_name])
                need_download = True
                if os.path.exists(local_path) and meta.get(meta_key) == file_sha:
                    need_download = False

                if need_download:
                    try:
                        r = requests.get(pdf_link, stream=True)
                        r.raise_for_status()
                        with open(local_path, 'wb') as out_f:
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    out_f.write(chunk)
                        print(f"Scaricato/aggiornato: {local_path}")
                        meta[meta_key] = file_sha
                        try:
                            meta[meta_key + '::updated_at'] = datetime.datetime.utcnow().isoformat()
                        except Exception:
                            meta[meta_key + '::updated_at'] = ''
                        save_meta(meta)
                    except requests.RequestException as e:
                        print(f"Errore download {pdf_link}: {e}")
                        continue

                rel_path = '/'.join([LOCAL_DOCS_DIR.replace('\\', '/'), urllib.parse.quote(safe_folder), urllib.parse.quote(safe_folder_name), urllib.parse.quote(safe_name)])

                html_output += f"""
                        <div class=\"subfolder\">\n                            <div class=\"folder-header\" data-folder=\"{data_folder_id}\">\n                                <h4><span class=\"folder-icon\">📁</span> {folder_name}</h4>\n                                <span class=\"toggle-icon\">+</span>\n                            </div>\n                            <div class=\"folder-content\" id=\"{data_folder_id}-content\">\n                                <ul>\n                                    <li>\n                                        <a href=\"{rel_path}\" target=\"_blank\" rel=\"noopener noreferrer\">\n                                            <span class=\"file-icon\">📄</span> {pdf_name}\n                                        </a>\n                                    </li>\n                                </ul>\n                            </div>\n                        </div>\n"""
    return html_output

    # (note: caller may save meta)

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

    # 3.1 Processa Diario di bordo
    diario_html = process_simple_folder_content("DIARIO DI BORDO")
    update_index_file("<!-- START_DIARIO -->", "<!-- END_DIARIO -->", diario_html)

    # 3.2 Processa Dichiarazione impegni
    dichiarazione_html = process_simple_folder_content("DICHIARAZIONE IMPEGNI")
    update_index_file("<!-- START_DICHIARAZIONE -->", "<!-- END_DICHIARAZIONE -->", dichiarazione_html)

    # 3.3 Processa Glossario
    glossario_html = process_simple_folder_content("GLOSSARIO")
    update_index_file("<!-- START_GLOSSARIO -->", "<!-- END_GLOSSARIO -->", glossario_html)

    # 4. Processa Verbali Interni
    interni_html = process_nested_folder("VERBALI/Interni", "Interni")
    update_index_file("<!-- START_VERBALI_INTERNI -->", "<!-- END_VERBALI_INTERNI -->", interni_html)

    # 5. Processa Verbali Esterni
    esterni_html = process_nested_folder("VERBALI/Esterni", "Esterni")
    update_index_file("<!-- START_VERBALI_ESTERNI -->", "<!-- END_VERBALI_ESTERNI -->", esterni_html)
    
    print("Sincronizzazione completata.")

if __name__ == "__main__":
    main()