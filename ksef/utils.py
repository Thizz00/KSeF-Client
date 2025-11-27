"""Utility functions for KSeF"""

from pathlib import Path
from typing import List
from ksef.constants import DEFAULT_ENCODING, DEFAULT_FILE_PATTERN


def load_invoice_from_file(file_path: str) -> str:
    return _read_file(file_path)


def load_invoices_from_directory(
    directory_path: str, pattern: str = DEFAULT_FILE_PATTERN
) -> List[str]:
    directory = Path(directory_path)
    xml_files = _get_sorted_files(directory, pattern)
    return [_read_file(f) for f in xml_files]


def _read_file(file_path: str) -> str:
    with open(file_path, "r", encoding=DEFAULT_ENCODING) as f:
        return f.read()


def _get_sorted_files(directory: Path, pattern: str) -> List[Path]:
    return sorted(directory.glob(pattern))
