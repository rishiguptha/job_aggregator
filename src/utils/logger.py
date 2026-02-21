import logging
import os
from src.config.settings import BASE_DIR

LOG_DIR = BASE_DIR / "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "job_alert_v2.log"),
    ],
)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
