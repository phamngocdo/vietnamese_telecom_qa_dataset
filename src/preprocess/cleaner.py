import os
import re
import json
from typing import List, Dict, Tuple

from src.preprocess.config import PARSED_JSON_DIR, CLEANED_JSON_DIR, load_source_config, ensure_dir_exists, MAX_CHUNK_WORDS, OVERLAP_WORDS

def clean_text_content(text: str) -> str:
    if not text:
        return ""
    text = text.replace("…", ".").replace("·", ".").replace("‧", ".").replace("∙", ".").replace("⋯", ".")
    text = text.replace("–", "-").replace("—", "-").replace("―", "-").replace("_", "-")
    text = re.sub(r'([.\-=_*#~])\1{2,}', r'\1', text)
    text = re.sub(r'(?:[\.\-\–\—\·\∙\⋯\=_*~]{4,})', ' ', text)
    text = re.sub(r'[\x00-\x1F\x7F]', '', text) 
    text = re.sub(r'^[\W_]{3,}$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def split_text_by_words(text, max_words, overlap_words):
    words = text.split()
    chunks = []
    stride = max(max_words - overlap_words, 1)
    for start in range(0, len(words), stride):
        end = min(start + max_words, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == len(words):
            break
    return chunks


def build_source_origin(file_path: str, source_config):
    parts = file_path.split(os.sep)
    for key in source_config.keys():
        if key in parts:
            label = source_config[key]
            sub_path = parts[parts.index(key) + 1:]
            if key == "arxiv" and sub_path:
                sub_path[-1] = os.path.splitext(sub_path[-1])[0]
            else:
                sub_path = sub_path[:-1]
            return f"{label}/{'/'.join(sub_path)}" if sub_path else label
    return os.path.basename(file_path)


def _is_block_inside_table(block_bbox: List[float], table_bboxes: List[Tuple[float]]) -> bool:
    b_x0, b_y0, b_x1, b_y1 = block_bbox
    
    for t_bbox in table_bboxes:
        t_x0, t_y0, t_x1, t_y1 = t_bbox
        
        block_center_x = (b_x0 + b_x1) / 2
        block_center_y = (b_y0 + b_y1) / 2
        
        if (t_x0 <= block_center_x <= t_x1) and (t_y0 <= block_center_y <= t_y1):
            return True
    return False


def format_table_to_string(table_data: List[List[str]], caption: str, surrounding_context: str) -> str:
    if not table_data or len(table_data) < 2:
        return ""

    headers = [h.strip() if h else f"Col_{i}" for i, h in enumerate(table_data[0])]
    
    formatted = ""
    if surrounding_context:
        formatted = f"[SURROUNDING CONTEXT]: {surrounding_context}\n"
    if caption:
        formatted += f"[CAPTION: {clean_text_content(caption)}]\n" 
        
    formatted += "[TECHNICAL TABLE START]\n"

    for i, row in enumerate(table_data[1:]):
        cells = []
        for j, value in enumerate(row):
            header = headers[j] if j < len(headers) else f"Col_{j+1}"
            value = value.strip() if value else "N/A"
            cells.append(f"{header}: {value}")
        formatted += f"ROW {i+1}: " + " | ".join(cells) + "\n"

    formatted += "[TECHNICAL TABLE END]"
    return formatted


def clean_and_chunk_data(parsed_json_path: str, source_config: Dict) -> List[Dict]:
    with open(parsed_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    document_id = os.path.basename(parsed_json_path)
    all_chunks = []
    origin = build_source_origin(parsed_json_path, source_config)

    table_bboxes_by_page = {}
    for table in data.get("tables", []):
        page_no = table.get("page_no")
        if page_no not in table_bboxes_by_page:
            table_bboxes_by_page[page_no] = []
        table_bboxes_by_page[page_no].append(list(table.get("bbox", (0,0,0,0))))

    full_text = ""
    for page in data.get("pages", []):
        page_no = page.get("page_no")
        table_bboxes_on_this_page = table_bboxes_by_page.get(page_no, [])
        
        for b in page.get("blocks", []):
            if isinstance(b, dict) and b.get("text"):
                
                if _is_block_inside_table(b.get("bbox", []), table_bboxes_on_this_page):
                    continue
                    
                cleaned_text = clean_text_content(b["text"])
                if cleaned_text:
                    full_text += cleaned_text + "\n\n"

    if full_text:
        chunks = split_text_by_words(full_text.strip(), MAX_CHUNK_WORDS, OVERLAP_WORDS)
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "context": chunk,
                "source": { "document_id": document_id, "origin": origin, "chunk_type": "TEXT_BLOCK", "chunk_order": i + 1, "length_words": len(chunk.split())}
            })

    for table in data.get("tables", []):
        raw_table = table.get("data")
        caption = table.get("caption", "")
        surrounding_context = table.get("surrounding_context", "")
        
        if raw_table:
            table_context = format_table_to_string(raw_table, caption, surrounding_context)
            if table_context:
                all_chunks.append({
                    "context": table_context,
                    "source": { "document_id": document_id, "origin": origin, "chunk_type": "TECHNICAL_TABLE", "page_no": table.get("page_no"), "table_index": table.get("table_index"), "length_words": len(table_context.split())}
                })

    return all_chunks


def clean_all_parsed_documents():
    if not os.path.exists(PARSED_JSON_DIR):
        print(f"Parsed JSON directory not found: {PARSED_JSON_DIR}")
        return

    os.makedirs(CLEANED_JSON_DIR, exist_ok=True)
    source_config = load_source_config()

    for root, _, files in os.walk(PARSED_JSON_DIR):
        for file_name in files:
            if not file_name.endswith(".json"):
                continue

            parsed_path = os.path.join(root, file_name)
            rel_path = os.path.relpath(root, PARSED_JSON_DIR)
            output_dir = os.path.join(CLEANED_JSON_DIR, rel_path)
            os.makedirs(output_dir, exist_ok=True)
            cleaned_path = os.path.join(output_dir, file_name)

            if os.path.exists(cleaned_path):
                 print(f"Skipping (already cleaned): {file_name}")
                 continue

            print(f"Cleaning: {file_name}")
            try:
                chunks = clean_and_chunk_data(parsed_path, source_config)
                with open(cleaned_path, "w", encoding="utf-8") as f:
                    json.dump(chunks, f, ensure_ascii=False, indent=4)
                print(f"Saved {len(chunks)} chunks -> {cleaned_path}")
            except Exception as e:
                print(f"Error cleaning {file_name}: {e}")