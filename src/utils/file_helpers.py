import zipfile
import os
import subprocess
import json
import shutil

def extract_nested_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
        for f in zip_ref.namelist():
            if f.endswith(".zip"):
                nested_path = os.path.join(extract_to, f)
                extract_nested_zip(nested_path, os.path.join(extract_to, f.replace(".zip","")))

def convert_doc_to_pdf(file_path, output_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    libreoffice_cmd = "libreoffice" if os.name != "nt" else "soffice"
    if subprocess.call([libreoffice_cmd, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
        raise EnvironmentError("LibreOffice is not installed or not found in PATH.")

    try:
        subprocess.run(
            [libreoffice_cmd, "--headless", "--convert-to", "pdf", file_path, "--outdir", os.path.dirname(output_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        converted_file = os.path.splitext(file_path)[0] + ".pdf"
        if os.path.exists(converted_file):
            os.rename(converted_file, output_path)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to convert {file_path} to PDF: {e}")
    
def merge_json(path, dict):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        existing_data.update(dict)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=4)
    else:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(dict, f, indent=4)

def create_folder(path):
    try:
        os.makedirs(path, exist_ok=False)
        return True, "Created!"
    except Exception as e:
        return False, str(e)

def delete_path(path):
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        return True, "Deleted!"
    except Exception as e:
        return False, str(e)

def save_uploaded_files(files, target):
    if not os.path.exists(target):
        os.makedirs(target)
    cnt = 0
    for f in files:
        fp = os.path.join(target, f.name)
        try:
            with open(fp, "wb") as out:
                out.write(f.getbuffer())
            cnt += 1
        except Exception:
            pass
    return cnt