import logging
import os
import sys
from datetime import datetime


class Logger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance

    def _initialize_logger(self):
        self.logger = logging.getLogger("AstroApp")
        self.logger.setLevel(logging.DEBUG)

        if self.logger.handlers:
            self.logger.handlers.clear()

        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        parent_dir = os.path.dirname(project_root)

        logs_dir = os.path.join(parent_dir, 'logs')
        os.makedirs(logs_dir, exist_ok=True)

        self.logs_dir = logs_dir

        log_file = os.path.join(logs_dir, f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(service)s] %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        self.log_file = log_file

        self.logger.info("Logger initialized", extra={'service': 'Logger'})
        self.logger.info(f"Project root: {project_root}", extra={'service': 'Logger'})
        self.logger.info(f"Logs directory: {logs_dir}", extra={'service': 'Logger'})
        self.logger.info(f"Current log file: {log_file}", extra={'service': 'Logger'})

    def debug(self, service, message):
        self.logger.debug(message, extra={'service': service})

    def info(self, service, message):
        self.logger.info(message, extra={'service': service})

    def warning(self, service, message):
        self.logger.warning(message, extra={'service': service})

    def error(self, service, message):
        self.logger.error(message, extra={'service': service})

    def critical(self, service, message):
        self.logger.critical(message, extra={'service': service})

    def get_log_file_path(self):
        return self.log_file