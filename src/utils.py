# utils.py
#
# Module for utility functions used across the project. This includes functions
# for handling file paths, logging, and any other common tasks that are needed
# in our extraction and analysis pipeline.

import inspect
from pathlib import Path


def normalize_path(path: str) -> Path:
    """
    Normalize a file path to ensure it is in a consitent format, to be called
    before any file operations.
    Args:
        path (str): a file-relative or absolute path as a string.
    Returns:
        a Path object representing the normalized path.
    """
    caller_path = inspect.stack()[1].filename
    caller_dir = Path(caller_path).parent
    return (caller_dir / path).resolve()
