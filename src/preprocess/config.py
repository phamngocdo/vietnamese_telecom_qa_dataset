import os
import yaml

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

with open(os.path.join(PROJECT_ROOT, "config/path.yaml"), "r", encoding="utf-8") as f:
    data_paths = yaml.safe_load(f)

RAW_DATA_DIR = data_paths["raw"]
PARSED_JSON_DIR = data_paths["preprocessed"]["parsed"]
CLEANED_JSON_DIR = data_paths["preprocessed"]["cleaned"]
SOURCE_CONFIG_PATH = os.path.join(PROJECT_ROOT, "config/source-name.yaml")

with open(os.path.join(PROJECT_ROOT, "config/parameters.yaml"), "r", encoding="utf-8") as f:
    parameters = yaml.safe_load(f)

MAX_CHUNK_WORDS = parameters.get("max_chunk_words", 512)
OVERLAP_WORDS = parameters.get("overlap_words", 64)

with open(SOURCE_CONFIG_PATH, "r", encoding="utf-8") as f:
    SOURCE_CONFIG = yaml.safe_load(f)

def ensure_dir_exists(path: str):
    os.makedirs(path, exist_ok=True)