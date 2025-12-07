import os
import json
import fitz
import pdfplumber
from typing import Optional, Tuple

from src.preprocess.config import RAW_DATA_DIR, PARSED_JSON_DIR, ensure_dir_exists

def _clean_caption_text(text: str) -> str:
    if not text: return ""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return " ".join(lines)


def _find_table_caption_and_context(page: pdfplumber.page.Page, table_bbox: tuple) -> Tuple[Optional[str], str]:
    (x0, top, x1, bottom) = table_bbox
    caption = None
    H_PADDING = 50 
    search_x0 = max(0, x0 - H_PADDING)
    search_x1 = min(page.width, x1 + H_PADDING)
    
    search_box_above = (search_x0, max(0, top - 20), search_x1, top)
    search_box_below = (search_x0, bottom, search_x1, min(page.height, bottom + 20))

    caption_above = _clean_caption_text(page.crop(search_box_above).extract_text(x_tolerance=3))
    caption_below = _clean_caption_text(page.crop(search_box_below).extract_text(x_tolerance=3))
    
    if "bảng" in caption_above.lower() or "table" in caption_above.lower():
        caption = caption_above
    elif "bảng" in caption_below.lower() or "table" in caption_below.lower():
        caption = caption_below

    context_height = 75
    context_box_above = (0, max(0, top - context_height), page.width, top)
    context_box_below = (0, bottom, page.width, min(page.height, bottom + context_height))
    
    text_above = _clean_caption_text(page.crop(context_box_above).extract_text(x_tolerance=3))
    text_below = _clean_caption_text(page.crop(context_box_below).extract_text(x_tolerance=3))
    surrounding_context = (text_above + "\n" + text_below).strip()
    return caption, surrounding_context


def extract_tables(pdf_path: str):
    all_tables = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_index, page in enumerate(pdf.pages):
                tables_on_page = page.find_tables()
                if not tables_on_page: continue
                for table_index, table in enumerate(tables_on_page):
                    table_data = table.extract()
                    if not table_data: continue
                    caption, surrounding_context = _find_table_caption_and_context(page, table.bbox)
                    if caption: 
                        all_tables.append({
                            "page_no": page_index + 1,
                            "table_index": table_index,
                            "caption": caption,
                            "surrounding_context": surrounding_context,
                            "bbox": table.bbox, 
                            "data": table_data 
                        })
    except Exception as e:
        print(f"PDFPlumber table error: {e}")
    return all_tables


def parse_single_pdf_combined(file_path: str) -> Optional[str]:
    try:
        rel_path = os.path.relpath(file_path, RAW_DATA_DIR)
    except ValueError:
        rel_path = os.path.basename(file_path)

    output_rel_path = os.path.splitext(rel_path)[0] + ".json"
    output_path = os.path.join(PARSED_JSON_DIR, output_rel_path)
    
    ensure_dir_exists(os.path.dirname(output_path))

    if os.path.exists(output_path):
        print(f"  -> Skipped (Exists): {output_rel_path}")
        return output_path

    print(f"Parsing: {rel_path}")
    
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
                page_content = { "page_no": page_num + 1, "blocks": [] }
                for block in blocks:
                    if block[6] == 0: 
                        page_content["blocks"].append({
                            "text": block[4].strip(),
                            "bbox": list(block[:4]),
                            "block_id": block[5]
                        })
                doc_data["pages"].append(page_content)

        doc_data["tables"] = extract_tables(file_path)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(doc_data, f, ensure_ascii=False, indent=4)
            
        print(f"  -> Saved: {output_rel_path}")
        return output_path 
        
    except Exception as e:
        print(f"Critical error parsing {file_path}: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        return None


def get_all_pdf_files(root_dir: str):
    pdf_files = []
    for root, _, files in os.walk(root_dir):
        for f in files:
            if f.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(root, f))
    return pdf_files


def parse_all_documents():
    ensure_dir_exists(PARSED_JSON_DIR)
    pdf_files = get_all_pdf_files(RAW_DATA_DIR)
    print(f"Found {len(pdf_files)} PDF files to parse.\n")

    for index, file_path in enumerate(pdf_files):
        print(f"[{index + 1}/{len(pdf_files)}] Processing...")
        parse_single_pdf_combined(file_path)
