import os
from typing import Dict, Tuple
from ksef.client import KSeFClient
from ksef.utils import load_invoice_from_file, load_invoices_from_directory
from ksef.constants import DEFAULT_DOWNLOAD_DIR, DEFAULT_SEND_DIR


def send_xml_from_file(client: KSeFClient, xml_path: str) -> Dict:
    _validate_file_exists(xml_path)
    xml = load_invoice_from_file(xml_path)
    return client.send_single_invoice(xml)


def send_xmls_from_directory(
    client: KSeFClient, directory: str = DEFAULT_SEND_DIR
) -> Dict:
    _validate_directory_exists(directory)

    invoices = load_invoices_from_directory(directory)
    if not invoices:
        return _empty_results()

    return client.send_multiple_invoices(invoices)


def search_invoices_from_ksef(client: KSeFClient, **search_params) -> Dict:
    return client.search_invoices(**search_params)


def download_invoice(
    client: KSeFClient, ksef_number: str, output_dir: str = DEFAULT_DOWNLOAD_DIR
) -> Tuple[bool, str]:
    _ensure_directory(output_dir)
    output_file = _build_output_path(output_dir, ksef_number)
    success = client.download_invoice_to_file(ksef_number, output_file)
    return success, output_file


def _validate_file_exists(file_path: str):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")


def _validate_directory_exists(directory: str):
    if not os.path.isdir(directory):
        raise FileNotFoundError(f"Directory not found: {directory}")


def _ensure_directory(directory: str):
    os.makedirs(directory, exist_ok=True)


def _build_output_path(output_dir: str, ksef_number: str) -> str:
    return os.path.join(output_dir, f"{ksef_number}.xml")


def _empty_results() -> Dict:
    return {"total": 0, "successful": 0, "failed": 0, "results": []}
