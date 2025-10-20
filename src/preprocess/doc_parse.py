import os
import json
import fitz

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
RAW_DATA_DIR = os.path.join(PROJECT_ROOT, "data/raw/vn_spec")
PARSED_JSON_DIR = os.path.join(PROJECT_ROOT, "data/preprocessed/vn_spec")

def ensure_dir_exists(path: str):
    os.makedirs(path, exist_ok=True)

def get_all_pdf_files(root_dir: str):
    pdf_files = []
    for root, _, files in os.walk(root_dir):
        for f in files:
            if f.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(root, f))
    return pdf_files

def parse_single_pdf_with_fitz(file_path: str) -> dict:
    doc_data = {
        "file_name": os.path.basename(file_path),
        "pages": []
    }
    
    try:
        doc = fitz.open(file_path)
        doc_data["total_pages"] = doc.page_count
        
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
  
            blocks = page.get_text("blocks") 
            
            page_content = {
                "page_no": page_num + 1,
                "blocks": []
            }
            
            for block in blocks:
                if block[6] == 0:
                    page_content["blocks"].append({
                        "text": block[4].strip(),
                        "bbox": list(block[:4]),
                        "block_id": block[5]
                    })
                    
            doc_data["pages"].append(page_content)
        
        doc.close()
        return doc_data
        
    except Exception as e:
        print(f"PyMuPDF error: {e}")
        return {}


def parse_all_documents():
    ensure_dir_exists(PARSED_JSON_DIR)
    pdf_files = get_all_pdf_files(RAW_DATA_DIR)
    print(f"Found {len(pdf_files)} PDF files to parse.\n")

    for file_path in pdf_files:
        rel_path = os.path.relpath(file_path, RAW_DATA_DIR)
        output_rel_path = os.path.splitext(rel_path)[0] + ".json"
        output_path = os.path.join(PARSED_JSON_DIR, output_rel_path)
        
        ensure_dir_exists(os.path.dirname(output_path))

        if os.path.exists(output_path):
            print(f"Skipping (already exists): {rel_path}")
            continue

        print(f"Parsing: {rel_path}")
        
        dict_content = parse_single_pdf_with_fitz(file_path)
        
        if dict_content:
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(dict_content, f, ensure_ascii=False, indent=4)
                print(f"Saved: {output_rel_path}\n")
            except Exception as e:
                print(f"Error writing file {output_path}: {e}\n")
        else:
            print(f"Failed to parse content for {rel_path}\n")


if __name__ == "__main__":
    parse_all_documents()