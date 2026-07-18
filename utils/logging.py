import logging
from pathlib import Path

class RealtimeFileHandler(logging.FileHandler):
    """
    Custom FileHandler that flushes the file stream immediately on emit
    to ensure real-time logging to a file.
    """
    def emit(self, record):
        super().emit(record)
        self.flush()


def setup_logging(
    log_file: str = "logs/production.log",
    log_level: int = logging.INFO
) -> None:
    """
    Configures application-wide logging to write to a log file in real-time.
    """
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    log_format = (
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )
    formatter = logging.Formatter(log_format)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplication
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    file_handler = RealtimeFileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    root_logger.addHandler(file_handler)

    logging.info("Production logging initialized. Real-time file logging to: %s", log_path.absolute())
