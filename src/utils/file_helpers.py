import zipfile
import os
import subprocess

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