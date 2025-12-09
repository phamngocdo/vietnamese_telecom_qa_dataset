import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.append(PROJECT_ROOT)

from src.preprocess.parser import parse_all_documents, parse_single_pdf_combined
from src.preprocess.cleaner import clean_all_parsed_documents, clean_and_chunk_data

def preprocess_file(file_path: str):
    print("--- Parsing ---")
    parsed_file = parse_single_pdf_combined(file_path)
    print("--- Parsing Complete ---")
    print("--- Cleaning and Chunking ---")
    cleaned_file = clean_and_chunk_data(parsed_file)
    print("--- Cleaning and Chunking Complete ---")
    return cleaned_file

if __name__ == "__main__":
    print("========== START PARSING AND CLEANING PIPELINE ==========")
    parse_all_documents()
    print("--- Parsing Complete ---")
    clean_all_parsed_documents()
    print("========== PIPELINE ENDED SUCCESSFULLY ==========")