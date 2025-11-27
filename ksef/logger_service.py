import logging
from pathlib import Path
from ksef.constants import LOG_FORMAT, LOG_FORMAT_CONSOLE


class LoggerService:

    def __init__(self, name: str, log_file: str, level_file: str, level_console: str):
        self.logger = self._setup_logger(name, log_file, level_file, level_console)

    def _setup_logger(
        self, name: str, log_file: str, level_file: str, level_console: str
    ) -> logging.Logger:

        self._ensure_log_directory(log_file)

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        if not logger.handlers:
            self._add_file_handler(logger, log_file, level_file)
            self._add_console_handler(logger, level_console)

        return logger

    @staticmethod
    def _ensure_log_directory(log_file: str):
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    def _add_file_handler(self, logger: logging.Logger, log_file: str, level: str):
        handler = logging.FileHandler(log_file, encoding="utf-8")
        handler.setLevel(getattr(logging, level))
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)

    def _add_console_handler(self, logger: logging.Logger, level: str):
        handler = logging.StreamHandler()
        handler.setLevel(getattr(logging, level))
        handler.setFormatter(logging.Formatter(LOG_FORMAT_CONSOLE))
        logger.addHandler(handler)

    def info(self, message: str):
        self.logger.info(message)

    def debug(self, message: str):
        self.logger.debug(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def error(self, message: str, exc_info: bool = False):
        self.logger.error(message, exc_info=exc_info)
