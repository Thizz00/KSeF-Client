import os
import base64
import hashlib
from typing import Dict, Optional
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as crypto_padding
from cryptography import x509
from dateutil import parser
from ksef.constants import AES_KEY_SIZE, AES_BLOCK_SIZE, PKCS7_BLOCK_SIZE


class EncryptionManager:

    def __init__(self):
        self.symmetric_key: Optional[bytes] = None
        self.iv: Optional[bytes] = None

    def generate_session_keys(self, cert_b64: str) -> Dict:
        self._generate_random_keys()
        public_key = self._load_public_key(cert_b64)
        encrypted_key = self._encrypt_symmetric_key(public_key)

        return {
            "encryptedSymmetricKey": base64.b64encode(encrypted_key).decode("utf-8"),
            "initializationVector": base64.b64encode(self.iv).decode("utf-8"),
        }

    def encrypt_invoice(self, invoice_xml: str) -> Dict:
        self._validate_keys()

        invoice_bytes = invoice_xml.encode("utf-8")
        original_hash = self._calculate_hash(invoice_bytes)

        encrypted_data = self._encrypt_data(invoice_bytes)
        encrypted_hash = self._calculate_hash(encrypted_data)

        return {
            "invoiceHash": base64.b64encode(original_hash).decode("utf-8"),
            "invoiceSize": len(invoice_bytes),
            "encryptedInvoiceHash": base64.b64encode(encrypted_hash).decode("utf-8"),
            "encryptedInvoiceSize": len(encrypted_data),
            "encryptedInvoiceContent": base64.b64encode(encrypted_data).decode("utf-8"),
        }

    @staticmethod
    def encrypt_token(token: str, timestamp_iso: str, public_key_b64: str) -> str:
        public_key = EncryptionManager._load_public_key(public_key_b64)
        token_data = EncryptionManager._prepare_token_data(token, timestamp_iso)
        encrypted = EncryptionManager._encrypt_with_rsa(token_data, public_key)

        return base64.b64encode(encrypted).decode("utf-8")

    def _generate_random_keys(self):
        self.symmetric_key = os.urandom(AES_KEY_SIZE)
        self.iv = os.urandom(AES_BLOCK_SIZE)

    @staticmethod
    def _load_public_key(cert_b64: str):
        cert_der = base64.b64decode(cert_b64)
        cert = x509.load_der_x509_certificate(cert_der)
        return cert.public_key()

    def _encrypt_symmetric_key(self, public_key) -> bytes:
        return self._encrypt_with_rsa(self.symmetric_key, public_key)

    @staticmethod
    def _encrypt_with_rsa(data: bytes, public_key) -> bytes:
        return public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

    def _validate_keys(self):
        if not self.symmetric_key or not self.iv:
            raise RuntimeError("Session keys not initialized")

    @staticmethod
    def _calculate_hash(data: bytes) -> bytes:
        return hashlib.sha256(data).digest()

    def _encrypt_data(self, data: bytes) -> bytes:
        padded_data = self._apply_padding(data)
        return self._aes_encrypt(padded_data)

    @staticmethod
    def _apply_padding(data: bytes) -> bytes:
        padder = crypto_padding.PKCS7(PKCS7_BLOCK_SIZE).padder()
        return padder.update(data) + padder.finalize()

    def _aes_encrypt(self, data: bytes) -> bytes:
        cipher = Cipher(algorithms.AES(self.symmetric_key), modes.CBC(self.iv))
        encryptor = cipher.encryptor()
        return encryptor.update(data) + encryptor.finalize()

    @staticmethod
    def _prepare_token_data(token: str, timestamp_iso: str) -> bytes:
        timestamp_ms = EncryptionManager._parse_timestamp(timestamp_iso)
        return f"{token}|{timestamp_ms}".encode("utf-8")

    @staticmethod
    def _parse_timestamp(timestamp_iso: str) -> int:
        dt = parser.isoparse(timestamp_iso)
        return int(dt.timestamp() * 1000)
