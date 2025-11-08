import os
import json
import fitz
import pdfplumber
import re
from typing import List, Dict, Optional

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
RAW_DATA_DIR = os.path.join(PROJECT_ROOT, "data/raw/vn_spec/")
PARSED_JSON_DIR = os.path.join(PROJECT_ROOT, "data/preprocessed/parsed/vn_spec")

def ensure_dir_exists(path: str):
    os.makedirs(path, exist_ok=True)

def get_all_pdf_files(root_dir: str):
    pdf_files = []
    for root, _, files in os.walk(root_dir):
        for f in files:
            if f.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(root, f))
    return pdf_files

def clean_caption_text(text: str) -> str:
    if not text:
        return ""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return " ".join(lines)

def find_table_caption(page: pdfplumber.page.Page, table_bbox: tuple) -> Optional[str]:
    (x0, top, x1, bottom) = table_bbox
    
    search_box_above = (0, max(0, top - 25), page.width, top)
    search_box_below = (0, bottom, page.width, min(page.height, bottom + 25))

    caption_above = clean_caption_text(page.crop(search_box_above).extract_text())
    if "bảng" in caption_above.lower() or "table" in caption_above.lower():
        return caption_above
    caption_below = clean_caption_text(page.crop(search_box_below).extract_text())
    if "bảng" in caption_below.lower() or "table" in caption_below.lower():
        return caption_below
    return None 
def extract_tables(pdf_path: str):
    extracted_tables = []
    
    last_valid_caption = None
    last_page_had_table_at_bottom = False

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                
                tables_on_page = page.find_tables()
                if not tables_on_page:
                    last_page_had_table_at_bottom = False
                    continue
                
                page_had_table_at_bottom = False

                for table_index, table in enumerate(tables_on_page):
                    table_data = table.extract()
                    if not table_data:
                        continue
                    
                    caption = find_table_caption(page, table.bbox)
                    
                    is_at_top = table.bbox[1] < 100 # Bảng nằm ở đầu trang
                    is_continuation = (not caption and last_page_had_table_at_bottom and is_at_top)

                    if caption:
                        last_valid_caption = caption
                    elif is_continuation:
                        caption = last_valid_caption
                    else:
                        continue
                    
                    extracted_tables.append({
                        "page_no": page_num + 1,
                        "table_index": table_index,
                        "caption": caption,
                        "data": table_data 
                    })
                    
                    if table.bbox[3] > (page.height - 50):
                         page_had_table_at_bottom = True
                
                last_page_had_table_at_bottom = page_had_table_at_bottom

    except Exception as e:
        print(f"PDFPlumber table error: {e}")
        return []
            
    if not extracted_tables:
        return []

    merged_tables = []
    current_table = None

    for table in extracted_tables:
        if current_table is None:
            current_table = table
            continue
        
        if table['caption'] == current_table['caption']:
            current_data_no_header = table['data'][1:] if len(table['data']) > 1 else []
            current_table['data'].extend(current_data_no_header)
        else:
            merged_tables.append(current_table)
            current_table = table

    if current_table:
        merged_tables.append(current_table)

    return merged_tables

def parse_single_pdf_combined(file_path: str) -> dict:
    doc_data = {
        "file_name": os.path.basename(file_path),
        "pages": [],
        "tables": []
    }
    
    try:
        with fitz.open(file_path) as doc:
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

        doc_data["tables"] = extract_tables(file_path)
        
        return doc_data
        
    except Exception as e:
        print(f"Critical error during parsing: {e}")
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
        
        dict_content = parse_single_pdf_combined(file_path)
        
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
    print("========== Start the parsing process ==========")
    parse_all_documents()
    print("========== End of parsing ==========")