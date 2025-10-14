import logging
import os
from datetime import datetime

LOG_PATH = "logs"
if not os.path.exists(LOG_PATH):
    os.makedirs(LOG_PATH)

log_filename = os.path.join(LOG_PATH, f"{datetime.now().strftime('%Y-%m-%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)

def log_info(message: str):
    logging.info(message)

def log_warning(message: str):
    logging.warning(message)

def log_error(message: str):
    logging.error(message, exc_info=True)

def log_debug(message: str):
    logging.debug(message)