from typing import Optional
from ksef.http_client import HttpClient
from ksef.encryption import EncryptionManager
from ksef.logger_service import LoggerService
from ksef.constants import (
    ENDPOINT_SESSION_ONLINE,
    ENDPOINT_SESSION_CLOSE,
    ENDPOINT_PUBLIC_KEYS,
    HTTP_CREATED,
    HTTP_OK,
    HTTP_NO_CONTENT,
    HTTP_METHOD_NOT_ALLOWED,
    CERT_USAGE_SYMMETRIC_KEY,
    FORM_SYSTEM_CODE,
    FORM_SCHEMA_VERSION,
    FORM_VALUE,
)


class SessionService:

    def __init__(
        self,
        http_client: HttpClient,
        encryption: EncryptionManager,
        logger: LoggerService,
    ):
        self.http = http_client
        self.encryption = encryption
        self.logger = logger
        self.session_reference: Optional[str] = None

    def initialize_session(self, access_token: str) -> bool:
        self.logger.info("Generating session encryption...")

        cert = self._get_encryption_cert()
        if not cert:
            self.logger.error("Failed to get encryption certificate")
            return False

        encryption_data = self._generate_encryption(cert)
        if not encryption_data:
            return False

        return self._create_session(access_token, encryption_data)

    def terminate_session(self, access_token: str) -> bool:
        if not self.session_reference:
            return True

        endpoint = ENDPOINT_SESSION_CLOSE.format(session=self.session_reference)
        response = self.http.post_json(endpoint, {}, access_token)

        if response.status_code in [HTTP_OK, HTTP_NO_CONTENT, HTTP_METHOD_NOT_ALLOWED]:
            self.logger.info("Session closed")
            self.session_reference = None
            return True

        self.logger.warning(f"Session close warning: {response.status_code}")
        self.session_reference = None
        return True

    def _get_encryption_cert(self) -> Optional[str]:
        response = self.http.get_json(ENDPOINT_PUBLIC_KEYS)

        if response.status_code != HTTP_OK:
            return None

        data = response.json()
        return self._find_symmetric_key_cert(data)

    def _find_symmetric_key_cert(self, certificates: list) -> Optional[str]:
        for cert in certificates:
            usage = cert.get("usage", [])
            if CERT_USAGE_SYMMETRIC_KEY in usage:
                self.logger.info("SymmetricKeyEncryption certificate found")
                return cert.get("certificate")

        if certificates:
            self.logger.warning("Using first certificate for encryption")
            return certificates[0].get("certificate")

        return None

    def _generate_encryption(self, cert: str) -> Optional[dict]:
        try:
            return self.encryption.generate_session_keys(cert)
        except Exception as e:
            self.logger.error(f"Session encryption failed: {e}")
            return None

    def _create_session(self, access_token: str, encryption_data: dict) -> bool:
        payload = {
            "formCode": {
                "systemCode": FORM_SYSTEM_CODE,
                "schemaVersion": FORM_SCHEMA_VERSION,
                "value": FORM_VALUE,
            },
            "encryption": encryption_data,
        }

        response = self.http.post_json(ENDPOINT_SESSION_ONLINE, payload, access_token)

        if response.status_code != HTTP_CREATED:
            self.logger.error(f"Session initialization failed: {response.status_code}")
            return False

        data = response.json()
        self.session_reference = data.get("referenceNumber")
        valid_until = data.get("validUntil")

        self.logger.info(
            f"Session initialized: {self.session_reference} "
            f"(valid until {valid_until})"
        )
        return True
