import os
import yaml

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
RAW_DATA_DIR = os.path.join(PROJECT_ROOT, "data/raw/")
PARSED_JSON_DIR = os.path.join(PROJECT_ROOT, "data/preprocessed/parsed/")
CLEANED_JSON_DIR = os.path.join(PROJECT_ROOT, "data/preprocessed/cleaned/")
SOURCE_CONFIG_PATH = os.path.join(PROJECT_ROOT, "config/source-name.yaml")

MAX_CHUNK_WORDS = 512
OVERLAP_WORDS = 128

def load_source_config() -> dict:
    if os.path.exists(SOURCE_CONFIG_PATH):
        with open(SOURCE_CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}

def ensure_dir_exists(path: str):
    os.makedirs(path, exist_ok=True)