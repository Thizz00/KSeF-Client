import time
from typing import Dict, Optional
from ksef.http_client import HttpClient
from ksef.encryption import EncryptionManager
from ksef.logger_service import LoggerService
from ksef.rate_limiter import RateLimiter
from ksef.constants import (
    ENDPOINT_SESSION_INVOICES,
    ENDPOINT_SESSION_INVOICE_LIST,
    ENDPOINT_INVOICE_XML,
    ENDPOINT_INVOICE_METADATA,
    ENDPOINT_INVOICE_SEARCH,
    HTTP_ACCEPTED,
    HTTP_OK,
    STATUS_ACCEPTED,
    STATUS_PROCESSING,
    STATUS_PROCESSING_EXTENDED,
    STATUS_ERROR_THRESHOLD,
    DEFAULT_MAX_ATTEMPTS,
    DEFAULT_DELAY_SECONDS,
)


class InvoiceService:

    def __init__(
        self,
        http_client: HttpClient,
        encryption: EncryptionManager,
        logger: LoggerService,
        rate_limiter: RateLimiter,
        config,
    ):
        self.http = http_client
        self.encryption = encryption
        self.logger = logger
        self.rate_limiter = rate_limiter
        self.config = config

    def send_invoice(
        self, session_reference: str, access_token: str, invoice_xml: str
    ) -> Optional[str]:
        self.rate_limiter.wait_if_needed()

        encrypted_data = self._encrypt_invoice(invoice_xml)
        if not encrypted_data:
            return None

        return self._post_invoice(session_reference, access_token, encrypted_data)

    def poll_status(
        self,
        session_reference: str,
        access_token: str,
        reference_number: str,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        delay_sec: int = DEFAULT_DELAY_SECONDS,
    ) -> Optional[Dict]:
        self.logger.info(f"Checking invoice status: {reference_number}")

        for attempt in range(1, max_attempts + 1):
            if attempt > 1:
                time.sleep(delay_sec)

            status = self._check_status(
                session_reference, access_token, reference_number
            )

            if status is None:
                self.logger.debug(
                    f"Invoice not in list yet (attempt {attempt}/{max_attempts})"
                )
                continue

            result = self._process_status(
                status, reference_number, attempt, max_attempts
            )
            if result != "continue":
                return result

        self.logger.error(f"Max attempts ({max_attempts}) reached")
        return None

    def get_invoice_xml(self, ksef_number: str, access_token: str) -> Optional[str]:
        self.logger.info(f"Downloading invoice: {ksef_number}")

        endpoint = ENDPOINT_INVOICE_XML.format(number=ksef_number)
        response = self.http.get_xml(endpoint, access_token)

        if response.status_code == HTTP_OK:
            self.logger.info(f"Invoice downloaded: {len(response.text)} bytes")
            return response.text

        self.logger.error(f"Failed to download invoice: {response.status_code}")
        return None

    def get_metadata(self, ksef_number: str, access_token: str) -> Optional[Dict]:
        self.logger.info(f"Getting metadata: {ksef_number}")

        endpoint = ENDPOINT_INVOICE_METADATA.format(number=ksef_number)
        response = self.http.get_json(endpoint, access_token)

        if response.status_code == HTTP_OK:
            self.logger.info("Metadata retrieved")
            return response.json()

        self.logger.error(f"Failed to get metadata: {response.status_code}")
        return None

    def search_invoices(self, access_token: str, **params) -> Optional[Dict]:
        query_params = self._extract_query_params(params)
        body = self._build_search_body(params)

        self.logger.info("Searching invoices...")
        response = self.http.post_json(
            ENDPOINT_INVOICE_SEARCH, body, access_token, query_params
        )

        if response.status_code == HTTP_OK:
            results = response.json()
            count = len(results.get("invoices", []))
            self.logger.info(f"Found {count} invoices")
            return results

        self.logger.error(f"Search failed: {response.status_code}")
        return None

    def _encrypt_invoice(self, invoice_xml: str) -> Optional[Dict]:
        try:
            return self.encryption.encrypt_invoice(invoice_xml)
        except Exception as e:
            self.logger.error(f"Invoice encryption failed: {e}")
            return None

    def _post_invoice(
        self, session_reference: str, access_token: str, encrypted_data: Dict
    ) -> Optional[str]:
        endpoint = ENDPOINT_SESSION_INVOICES.format(session=session_reference)
        response = self.http.post_json(endpoint, encrypted_data, access_token)

        if response.status_code == HTTP_ACCEPTED:
            reference_number = response.json().get("referenceNumber")
            self.logger.info(f"Invoice sent: {reference_number}")
            return reference_number

        self.logger.error(f"Invoice send failed: {response.status_code}")
        return None

    def _check_status(
        self, session_reference: str, access_token: str, reference_number: str
    ) -> Optional[Dict]:
        endpoint = ENDPOINT_SESSION_INVOICE_LIST.format(session=session_reference)
        response = self.http.get_json(endpoint, access_token)

        if response.status_code != HTTP_OK:
            self.logger.error(f"Failed to get invoice list: {response.status_code}")
            return None

        data = response.json()
        invoices = data.get("invoices", [])

        return next(
            (inv for inv in invoices if inv.get("referenceNumber") == reference_number),
            None,
        )

    def _process_status(
        self, invoice: Dict, reference_number: str, attempt: int, max_attempts: int
    ):
        status_info = invoice.get("status", {})
        code = status_info.get("code")
        description = status_info.get("description", "")

        if code == STATUS_ACCEPTED:
            return self._handle_accepted(invoice, reference_number)

        if code in [STATUS_PROCESSING, STATUS_PROCESSING_EXTENDED]:
            self.logger.debug(
                f"Invoice processing (code {code}, attempt {attempt}/{max_attempts})"
            )
            return "continue"

        if code >= STATUS_ERROR_THRESHOLD:
            return self._handle_rejected(code, description, reference_number)

        self.logger.warning(f"Unknown status code: {code}")
        return "continue"

    def _handle_accepted(self, invoice: Dict, reference_number: str) -> Dict:
        ksef_number = invoice.get("ksefNumber")
        link = self.config.get_invoice_url(ksef_number)

        self.logger.info(f"Invoice accepted: {ksef_number}")
        return {
            "ksefNumber": ksef_number,
            "status": "accepted",
            "link": link,
            "referenceNumber": reference_number,
        }

    def _handle_rejected(
        self, code: int, description: str, reference_number: str
    ) -> Dict:
        self.logger.error(f"Invoice rejected (code {code}): {description}")
        return {
            "status": "rejected",
            "code": code,
            "description": description,
            "referenceNumber": reference_number,
        }

    @staticmethod
    def _extract_query_params(params: Dict) -> Dict:
        return {
            "sortOrder": params.get("sort_order", "desc"),
            "pageOffset": params.get("page_offset", 0),
            "pageSize": params.get("page_size", 250),
        }

    @staticmethod
    def _build_search_body(params: Dict) -> Dict:
        body = {
            "subjectType": params["subject_type"],
            "dateRange": {"dateType": params["date_type"], "from": params["date_from"]},
        }

        InvoiceService._add_optional_params(body, params)
        return body

    @staticmethod
    def _add_optional_params(body: Dict, params: Dict):
        optional_fields = {
            "date_to": ("dateRange", "to"),
            "ksef_number": ("ksefNumber",),
            "invoice_number": ("invoiceNumber",),
            "seller_nip": ("sellerNip",),
            "buyer_identifier": ("buyerIdentifier",),
            "amount": ("amount",),
            "currency_codes": ("currencyCodes",),
            "invoicing_mode": ("invoicingMode",),
            "is_self_invoicing": ("isSelfInvoicing",),
            "form_type": ("formType",),
            "invoice_types": ("invoiceTypes",),
            "has_attachment": ("hasAttachment",),
        }

        for param_key, body_path in optional_fields.items():
            value = params.get(param_key)
            if value is not None:
                if len(body_path) == 2:
                    body[body_path[0]][body_path[1]] = value
                else:
                    body[body_path[0]] = value
