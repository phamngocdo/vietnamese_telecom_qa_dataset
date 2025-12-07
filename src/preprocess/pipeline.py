import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.append(PROJECT_ROOT)

from src.preprocess.parser import parse_all_documents, parse_single_pdf_combined
from src.preprocess.cleaner import clean_all_parsed_documents, clean_and_chunk_data

def preprocess_file(file_path: str):
    parse_single_pdf_combined(file_path)
    clean_and_chunk_data(file_path)

if __name__ == "__main__":
    print("========== START PARSING AND CLEANING PIPELINE ==========")
    parse_all_documents()
    print("--- Parsing Complete ---")
    clean_all_parsed_documents()
    print("========== PIPELINE ENDED SUCCESSFULLY ==========")