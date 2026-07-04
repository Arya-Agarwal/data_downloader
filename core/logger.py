from pathlib import Path
from datetime import datetime
from loguru import logger

from config import LOG_DIR


def setup_logger():
    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    log_file = LOG_DIR / f"{datetime.now().strftime('%Y%m%d')}.log"

    logger.remove()

    logger.add(
        log_file,
        rotation="10 MB",
        level="INFO"
    )

    logger.add(
        lambda msg: print(msg, end=""),
        level="INFO"
    )

    return logger


log = setup_logger()