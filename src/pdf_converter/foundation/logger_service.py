import sys
import logging
import datetime
from typing import Optional
from pdf_converter.utils.app_constants import LogColors

class CustomFormatter(logging.Formatter):
    def formatTime(self, record: logging.LogRecord, datefmt: Optional[str] = None) -> str:
        dt = datetime.datetime.fromtimestamp(record.created, datetime.timezone.utc)
        return dt.strftime('%Y-%m-%d %H:%M:%S.%f') + "+00:00"

    def format(self, record: logging.LogRecord) -> str:
        original_msg = record.msg
        if record.levelno == logging.ERROR:
            record.msg = f"{LogColors.RED}ERROR: {original_msg}{LogColors.RESET}"
        elif record.levelno == logging.WARNING:
            if isinstance(original_msg, str) and original_msg.startswith("[OPT]"):
                record.msg = f"{LogColors.BLUE}WARNING: {original_msg}{LogColors.RESET}"
            else:
                record.msg = f"{LogColors.YELLOW}WARNING: {original_msg}{LogColors.RESET}"
        
        res = super().format(record)
        record.msg = original_msg
        return res

def setup_logger(name: str = "AppLogger") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = CustomFormatter(fmt="%(asctime)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

logger = setup_logger()
