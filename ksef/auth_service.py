import time
from typing import Dict, Optional
from ksef.http_client import HttpClient
from ksef.encryption import EncryptionManager
from ksef.logger_service import LoggerService
from ksef.constants import (
    ENDPOINT_AUTH_CHALLENGE,
    ENDPOINT_AUTH_KSEF_TOKEN,
    ENDPOINT_AUTH_STATUS,
    ENDPOINT_AUTH_REDEEM,
    ENDPOINT_PUBLIC_KEYS,
    HTTP_OK,
    HTTP_ACCEPTED,
    CONTEXT_TYPE_NIP,
    STATUS_ACCEPTED,
    AUTH_WAIT_SECONDS,
    CERT_TYPE_ENCRYPTION,
)


class AuthService:

    def __init__(self, http_client: HttpClient, logger: LoggerService, nip: str):
        self.http = http_client
        self.logger = logger
        self.nip = nip
        self.authentication_token: Optional[str] = None
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None

    def authenticate(self, ksef_token: str) -> bool:
        self.logger.info("Starting authentication...")

        challenge_data = self._get_challenge()
        if not challenge_data:
            return False

        public_key = self._get_public_key()
        if not public_key:
            return False

        encrypted_token = self._encrypt_token(
            ksef_token, challenge_data["timestamp"], public_key
        )
        if not encrypted_token:
            return False

        if not self._request_authentication(
            challenge_data["challenge"], encrypted_token
        ):
            return False

        if not self._wait_for_completion():
            return False

        if not self._redeem_token():
            return False

        self.logger.info("Authentication complete")
        return True

    def _get_challenge(self) -> Optional[Dict]:
        payload = {"contextIdentifier": {"type": CONTEXT_TYPE_NIP, "value": self.nip}}

        response = self.http.post_json(ENDPOINT_AUTH_CHALLENGE, payload)

        if response.status_code == HTTP_OK:
            self.logger.info("Challenge received")
            return response.json()

        self.logger.error(f"Challenge failed: {response.status_code}")
        return None

    def _get_public_key(self) -> Optional[str]:
        response = self.http.get_json(ENDPOINT_PUBLIC_KEYS)

        if response.status_code != HTTP_OK:
            self.logger.error(f"Failed to get public key: {response.status_code}")
            return None

        data = response.json()
        return self._extract_encryption_cert(data)

    def _extract_encryption_cert(self, certificates: list) -> Optional[str]:
        for cert in certificates:
            if cert.get("type") == CERT_TYPE_ENCRYPTION:
                self.logger.info("Encryption certificate found")
                return cert.get("certificate")

        if certificates:
            self.logger.info("Using first certificate")
            return certificates[0].get("certificate")

        self.logger.error("No certificates found")
        return None

    def _encrypt_token(
        self, token: str, timestamp: str, public_key: str
    ) -> Optional[str]:
        self.logger.info("Encrypting token...")
        try:
            return EncryptionManager.encrypt_token(token, timestamp, public_key)
        except Exception as e:
            self.logger.error(f"Token encryption failed: {e}")
            return None

    def _request_authentication(self, challenge: str, encrypted_token: str) -> bool:
        payload = {
            "encryptedToken": encrypted_token,
            "challenge": challenge,
            "contextIdentifier": {"type": CONTEXT_TYPE_NIP, "value": self.nip},
        }

        response = self.http.post_json(ENDPOINT_AUTH_KSEF_TOKEN, payload)

        if response.status_code != HTTP_ACCEPTED:
            self.logger.error(f"Authentication failed: {response.status_code}")
            return False

        data = response.json()
        self.authentication_token = data.get("authenticationToken", {}).get("token")
        auth_reference = data.get("referenceNumber")

        self.logger.info(f"Authentication token received: {auth_reference}")
        self._store_auth_reference(auth_reference)
        return True

    def _store_auth_reference(self, reference: str):
        self.auth_reference = reference

    def _wait_for_completion(self) -> bool:
        time.sleep(AUTH_WAIT_SECONDS)

        endpoint = ENDPOINT_AUTH_STATUS.format(reference=self.auth_reference)
        response = self.http.get_json(endpoint, self.authentication_token)

        if response.status_code != HTTP_OK:
            self.logger.error(f"Failed to get auth status: {response.status_code}")
            return False

        return self._check_auth_status(response.json())

    def _check_auth_status(self, data: Dict) -> bool:
        status = data.get("status", {})
        status_code = status.get("code") if isinstance(status, dict) else None

        if status_code == STATUS_ACCEPTED:
            self.logger.info("Authentication completed")
            return True

        self.logger.error(f"Authentication status: {status}")
        return False

    def _redeem_token(self) -> bool:
        response = self.http.post_json(
            ENDPOINT_AUTH_REDEEM, {}, self.authentication_token
        )

        if response.status_code != HTTP_OK:
            self.logger.error(f"Token redeem failed: {response.status_code}")
            return False

        self._extract_tokens(response.json())
        self.logger.info("Access and refresh tokens obtained")
        return True

    def _extract_tokens(self, data: Dict):
        self.access_token = data.get("accessToken", {}).get("token")
        self.refresh_token = data.get("refreshToken", {}).get("token")
