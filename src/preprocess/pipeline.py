import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.append(PROJECT_ROOT)

from src.preprocess.parser import parse_all_documents, parse_single_pdf_combined
from src.preprocess.cleaner import clean_all_parsed_documents, clean_and_chunk_data
from src.utils.logger import log_info

def preprocess_file(file_path: str):
    ("--- Parsing ---")
    parsed_file = parse_single_pdf_combined(file_path)
    log_info("--- Parsing Complete ---")
    log_info("--- Cleaning and Chunking ---")
    cleaned_file = clean_and_chunk_data(parsed_file)
    log_info("--- Cleaning and Chunking Complete ---")
    return cleaned_file

if __name__ == "__main__":
    log_info("========== START PARSING AND CLEANING PIPELINE ==========")
    parse_all_documents()
    log_info("--- Parsing Complete ---")
    clean_all_parsed_documents()
    log_info("========== PIPELINE ENDED SUCCESSFULLY ==========")