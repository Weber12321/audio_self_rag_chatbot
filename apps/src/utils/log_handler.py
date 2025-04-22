"""
A function to setup a log handler in the application.
"""

import os
import logging
from datetime import datetime


def setup_logger(
    logger_name="viki_lab",
    log_level=logging.INFO,
    log_directory=None,
    log_filename=None,
    console_output=True,
):
    """
    Sets up a logger with file and optional console handlers.

    Args:
        logger_name (str): Name of the logger
        log_level (int): Logging level (e.g., logging.INFO, logging.DEBUG)
        log_directory (str, optional): Directory to save log files. If None, defaults to a logs folder in the project root.
        log_filename (str, optional): Name of the log file. If None, generates a timestamped filename.
        console_output (bool): Whether to output logs to console

    Returns:
        logging.Logger: Configured logger object
    """
    # Get or create logger
    logger = logging.getLogger(logger_name)

    # Only configure handlers if not already configured
    if not logger.handlers:
        logger.setLevel(log_level)

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Setup file handler
        if log_directory is None:
            # Default to a logs folder in the project root
            # Assumes this file is in project/apps/src/utils/
            project_root = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../../..")
            )
            log_directory = os.path.join(project_root, "logs")

        # Create log directory if it doesn't exist
        os.makedirs(log_directory, exist_ok=True)

        # Generate log filename if not provided
        if log_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_filename = f"{logger_name}_{timestamp}.log"

        log_file_path = os.path.join(log_directory, log_filename)

        # Create file handler
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Add console handler if requested
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        logger.info(f"Logger {logger_name} initialized. Logging to: {log_file_path}")

    return logger
