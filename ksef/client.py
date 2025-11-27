from typing import Dict, Optional, List
from pathlib import Path

from ksef.config import KSeFConfig
from ksef.http_client import HttpClient
from ksef.logger_service import LoggerService
from ksef.rate_limiter import RateLimiter
from ksef.encryption import EncryptionManager
from ksef.auth_service import AuthService
from ksef.session_service import SessionService
from ksef.invoice_service import InvoiceService
from ksef.constants import (
    EXTENDED_MAX_ATTEMPTS,
    EXTENDED_DELAY_SECONDS,
    DEFAULT_DOWNLOAD_DIR,
)


class KSeFClient:

    def __init__(self, config: KSeFConfig):
        self.config = config
        self._setup_services()

    def _setup_services(self):
        self.http = HttpClient(self.config.base_url)
        self.logger = LoggerService(
            "KSeFClient",
            self.config.log_file,
            self.config.log_level_file,
            self.config.log_level_console,
        )
        self.rate_limiter = RateLimiter(self.config.rate_limit)
        self.encryption = EncryptionManager()

        self.auth_service = AuthService(self.http, self.logger, self.config.nip)
        self.session_service = SessionService(self.http, self.encryption, self.logger)
        self.invoice_service = InvoiceService(
            self.http, self.encryption, self.logger, self.rate_limiter, self.config
        )

    @property
    def access_token(self) -> Optional[str]:
        return self.auth_service.access_token

    @property
    def session_reference(self) -> Optional[str]:
        return self.session_service.session_reference

    def authenticate(self) -> bool:
        return self.auth_service.authenticate(self.config.ksef_token)

    def initialize_session(self) -> bool:
        return self.session_service.initialize_session(self.access_token)

    def terminate_session(self) -> bool:
        return self.session_service.terminate_session(self.access_token)

    def send_invoice_to_session(self, invoice_xml: str) -> Optional[str]:
        return self.invoice_service.send_invoice(
            self.session_reference, self.access_token, invoice_xml
        )

    def poll_invoice_status(
        self, reference_number: str, max_attempts: int = 30, delay_sec: int = 1
    ) -> Optional[Dict]:
        return self.invoice_service.poll_status(
            self.session_reference,
            self.access_token,
            reference_number,
            max_attempts,
            delay_sec,
        )

    def get_invoice_xml(self, ksef_number: str) -> Optional[str]:
        return self.invoice_service.get_invoice_xml(ksef_number, self.access_token)

    def get_invoice_metadata(self, ksef_number: str) -> Optional[Dict]:
        return self.invoice_service.get_metadata(ksef_number, self.access_token)

    def search_invoices(self, **params) -> Optional[Dict]:
        return self.invoice_service.search_invoices(self.access_token, **params)

    def download_invoice_to_file(self, ksef_number: str, output_path: str) -> bool:
        invoice_xml = self.get_invoice_xml(ksef_number)

        if not invoice_xml:
            return False

        return self._save_to_file(invoice_xml, output_path)

    def download_multiple_invoices(
        self, ksef_numbers: List[str], output_dir: str = DEFAULT_DOWNLOAD_DIR
    ) -> Dict:
        results = self._init_download_results(len(ksef_numbers))

        self.logger.info(f"Downloading {len(ksef_numbers)} invoices...")

        for i, ksef_number in enumerate(ksef_numbers, 1):
            self._download_single(
                ksef_number, output_dir, i, len(ksef_numbers), results
            )

        self.logger.info(
            f"Download complete: {results['successful']}/{results['total']} successful"
        )
        return results

    def send_single_invoice(self, invoice_xml: str) -> Optional[Dict]:
        if not self._ensure_authenticated():
            return None

        if not self._ensure_session():
            return None

        return self._send_and_poll(invoice_xml)

    def send_multiple_invoices(self, invoices: List[str]) -> Dict:
        results = self._init_send_results(len(invoices))

        try:
            if not self._ensure_authenticated():
                return results

            if not self._ensure_session():
                return results

            return self._process_multiple_invoices(invoices, results)

        finally:
            self.terminate_session()

    def _save_to_file(self, content: str, output_path: str) -> bool:
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)

            self.logger.info(f"Invoice saved to: {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save file: {e}", exc_info=True)
            return False

    @staticmethod
    def _init_download_results(total: int) -> Dict:
        return {"total": total, "successful": 0, "failed": 0, "results": []}

    def _download_single(
        self, ksef_number: str, output_dir: str, index: int, total: int, results: Dict
    ):
        self.logger.info(f"Downloading {index}/{total}: {ksef_number}")

        filename = f"{ksef_number}.xml"
        output_path = f"{output_dir}/{filename}"

        success = self.download_invoice_to_file(ksef_number, output_path)

        if success:
            results["successful"] += 1
            results["results"].append(
                {"ksefNumber": ksef_number, "status": "success", "path": output_path}
            )
        else:
            results["failed"] += 1
            results["results"].append({"ksefNumber": ksef_number, "status": "failed"})

    def _ensure_authenticated(self) -> bool:
        if not self.access_token:
            self.logger.info("Authenticating...")
            if not self.authenticate():
                self.logger.error("Authentication failed")
                return False
        return True

    def _ensure_session(self) -> bool:
        if not self.session_reference:
            self.logger.info("Initializing session...")
            if not self.initialize_session():
                self.logger.error("Session initialization failed")
                return False
        return True

    def _send_and_poll(self, invoice_xml: str) -> Optional[Dict]:
        self.logger.info("Sending invoice...")
        reference_number = self.send_invoice_to_session(invoice_xml)

        if not reference_number:
            self.logger.error("Invoice send failed")
            return None

        self.logger.info("Checking invoice status...")
        result = self.poll_invoice_status(reference_number)

        if result and result.get("status") == "accepted":
            self.logger.info(f"Success! KSeF: {result['ksefNumber']}")
            return result

        self.logger.error("Failed to get KSeF number")
        return None

    @staticmethod
    def _init_send_results(total: int) -> Dict:
        return {"total": total, "successful": 0, "failed": 0, "results": []}

    def _process_multiple_invoices(self, invoices: List[str], results: Dict) -> Dict:
        self.logger.info(f"Sending {len(invoices)} invoices...")

        reference_numbers = self._send_all_invoices(invoices, results)

        if reference_numbers:
            self._poll_all_statuses(reference_numbers, results)

        self.logger.info(
            f"Summary: {results['successful']}/{results['total']} successful, "
            f"{results['failed']} failed"
        )
        return results

    def _send_all_invoices(self, invoices: List[str], results: Dict) -> List[str]:
        reference_numbers = []

        for i, invoice_xml in enumerate(invoices, 1):
            self.logger.info(f"Sending invoice {i}/{len(invoices)}...")
            reference = self.send_invoice_to_session(invoice_xml)

            if reference:
                reference_numbers.append(reference)
            else:
                self._add_failed_result(results, i, "Failed to send")

        return reference_numbers

    def _poll_all_statuses(self, reference_numbers: List[str], results: Dict):
        self.logger.info(f"Checking status of {len(reference_numbers)} invoices...")

        for i, reference in enumerate(reference_numbers, 1):
            self.logger.info(f"Checking invoice {i}/{len(reference_numbers)}...")

            result = self.poll_invoice_status(
                reference,
                max_attempts=EXTENDED_MAX_ATTEMPTS,
                delay_sec=EXTENDED_DELAY_SECONDS,
            )

            if result and result.get("status") == "accepted":
                self._add_success_result(results, i, result, reference)
            else:
                self._add_error_result(results, i, result, reference)

    @staticmethod
    def _add_failed_result(results: Dict, index: int, error: str):
        results["failed"] += 1
        results["results"].append({"index": index, "status": "failed", "error": error})

    @staticmethod
    def _add_success_result(results: Dict, index: int, result: Dict, reference: str):
        results["successful"] += 1
        results["results"].append(
            {
                "index": index,
                "status": "accepted",
                "ksefNumber": result["ksefNumber"],
                "link": result["link"],
                "referenceNumber": reference,
            }
        )

    @staticmethod
    def _add_error_result(
        results: Dict, index: int, result: Optional[Dict], reference: str
    ):
        results["failed"] += 1
        results["results"].append(
            {
                "index": index,
                "status": "rejected" if result else "unknown",
                "referenceNumber": reference,
                "error": result.get("description") if result else "Timeout",
            }
        )
