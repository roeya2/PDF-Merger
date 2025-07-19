import logging
import sys
from pathlib import Path
from typing import Dict, Any

from app.constants import LOGGER_NAME, DEFAULT_LOG_OUTPUT, DEFAULT_LOG_LEVEL, DEFAULT_LOG_FILE_PATH

def setup_application_logging(config: Dict[str, Any]):
    """
    Sets up the application logger based on the provided configuration.
    """
    log_level_str = config.get("log_level", DEFAULT_LOG_LEVEL).upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s'
    formatter = logging.Formatter(log_format)

    app_logger = logging.getLogger(LOGGER_NAME)
    app_logger.setLevel(log_level)
    app_logger.propagate = False

    # Clear any existing handlers
    if app_logger.hasHandlers():
        for handler in app_logger.handlers[:]:
             app_logger.removeHandler(handler)
             try: handler.close()
             except Exception: pass

    log_output_setting = config.get("log_output", DEFAULT_LOG_OUTPUT).lower()
    handlers_added = False

    # File Handler
    if log_output_setting in ["file", "both"]:
        try:
            log_file_path_str = config.get("log_file_path", DEFAULT_LOG_FILE_PATH)
            log_file_path = Path(log_file_path_str).resolve()
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
            file_handler.setFormatter(formatter)
            app_logger.addHandler(file_handler)
            handlers_added = True
            # Note: Initial print here is for critical startup info before logging is fully configured
            # print(f"INITIAL LOG: Logging to file: {log_file_path} (Level: {logging.getLevelName(log_level)})", flush=True)
        except Exception as e:
            print(f"Error setting up file logging to '{log_file_path_str}': {e}", file=sys.stderr, flush=True)
            if log_output_setting == "file": # Fallback only if file was requested exclusively
                log_output_setting = "console"
                print("Falling back to console logging due to file logging error.", file=sys.stderr, flush=True)

    # Console Handler
    if log_output_setting in ["console", "both"]:
        if not any(isinstance(h, logging.StreamHandler) for h in app_logger.handlers):
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setFormatter(formatter)
            app_logger.addHandler(console_handler)
            handlers_added = True
            # print(f"INITIAL LOG: Logging to console (Level: {logging.getLevelName(log_level)})", flush=True)

    if not handlers_added:
        app_logger.addHandler(logging.NullHandler())
        print(f"Warning: No logging handlers configured for '{LOGGER_NAME}' logger based on setting '{log_output_setting}'. Logs might not be saved or displayed.", file=sys.stderr, flush=True)

    app_logger.info(f"Logging configured. Level: {logging.getLevelName(app_logger.level)}, Output: {log_output_setting}")
