import os
import yaml

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

with open(os.path.join(PROJECT_ROOT, "config/path.yaml"), "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

RAW_DATA_PATH = config["raw"]