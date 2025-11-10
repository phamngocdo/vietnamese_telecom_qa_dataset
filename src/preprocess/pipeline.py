import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.append(PROJECT_ROOT)

from parser import parse_all_documents
from cleaner import clean_all_parsed_documents

if __name__ == "__main__":
    print("========== START PARSING AND CLEANING PIPELINE ==========")
    parse_all_documents()
    print("--- Parsing Complete ---")
    clean_all_parsed_documents()
    print("========== PIPELINE ENDED SUCCESSFULLY ==========")