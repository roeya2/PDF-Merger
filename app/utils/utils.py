import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from .constants import (
    LOGGER_NAME, DEFAULT_LOG_OUTPUT, DEFAULT_LOG_LEVEL, DEFAULT_LOG_FILE_PATH,
    PDF_EXTENSION, DOCX_EXTENSION, DOC_EXTENSION, EPUB_EXTENSION, ZIP_EXTENSION, RAR_EXTENSION,
    ERROR_FILE_NOT_FOUND, ERROR_UNSUPPORTED_FILE_TYPE
)

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


def resolve_file_path(path_str: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Resolves a file path and returns the resolved path and any error.

    Args:
        path_str: The file path string to resolve

    Returns:
        Tuple of (resolved_path, error_message). If successful, error_message is None.
    """
    try:
        path = Path(path_str)
        if not path.is_file():
            return None, ERROR_FILE_NOT_FOUND

        resolved_path = str(path.resolve())
        return resolved_path, None
    except Exception as e:
        return None, f"Path resolution error: {e}"


def get_file_extension(path: Path) -> str:
    """
    Gets the lowercase file extension from a path.

    Args:
        path: Path object

    Returns:
        Lowercase file extension (including the dot)
    """
    return path.suffix.lower()


def is_supported_file_type(file_extension: str) -> bool:
    """
    Checks if a file extension is supported by the application.

    Args:
        file_extension: Lowercase file extension (including the dot)

    Returns:
        True if the file type is supported
    """
    supported_extensions = [PDF_EXTENSION, DOCX_EXTENSION, DOC_EXTENSION, EPUB_EXTENSION]
    return file_extension in supported_extensions


def is_archive_file_type(file_extension: str) -> bool:
    """
    Checks if a file extension is an archive type.

    Args:
        file_extension: Lowercase file extension (including the dot)

    Returns:
        True if the file type is an archive
    """
    archive_extensions = [ZIP_EXTENSION, RAR_EXTENSION]
    return file_extension in archive_extensions


def validate_file_for_processing(path_str: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Validates a file for processing and returns resolved path and error.

    Args:
        path_str: The file path string to validate

    Returns:
        Tuple of (resolved_path, error_message). If successful, error_message is None.
    """
    resolved_path, error = resolve_file_path(path_str)
    if error:
        return None, error

    path = Path(resolved_path)
    file_extension = get_file_extension(path)

    if not is_supported_file_type(file_extension):
        return None, ERROR_UNSUPPORTED_FILE_TYPE.format(file_extension)

    return resolved_path, None


def get_supported_files_from_directory(directory_path: str) -> Tuple[list[str], list[Tuple[str, str]]]:
    """
    Scans a directory for supported files.

    Args:
        directory_path: Path to the directory to scan

    Returns:
        Tuple of (supported_files_list, problematic_files_list)
    """
    supported_files = []
    problematic_files = []

    try:
        for entry in Path(directory_path).iterdir():
            if entry.is_file():
                resolved_path, error = validate_file_for_processing(str(entry))
                if resolved_path:
                    supported_files.append(resolved_path)
                elif error:
                    problematic_files.append((str(entry), error))
    except OSError as e:
        problematic_files.append((directory_path, f"Could not read directory: {e}"))

    return supported_files, problematic_files
