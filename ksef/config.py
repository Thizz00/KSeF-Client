import os
from dataclasses import dataclass
from typing import Dict


@dataclass
class KSeFConfig:

    nip: str = os.getenv("KSEF_NIP", "")
    ksef_token: str = os.getenv("KSEF_TOKEN", "")
    environment: str = os.getenv("KSEF_ENV", "test")
    log_file: str = os.getenv("KSEF_LOG_FILE", "logs/ksef_log.log")
    rate_limit: int = int(os.getenv("KSEF_RATE_LIMIT", "10"))

    log_level_file: str = os.getenv("KSEF_LOG_LEVEL_FILE", "DEBUG")
    log_level_console: str = os.getenv("KSEF_LOG_LEVEL_CONSOLE", "INFO")

    @property
    def base_url(self) -> str:
        return self._get_environments().get(
            self.environment, self._get_environments()["test"]
        )

    @staticmethod
    def _get_environments() -> Dict[str, str]:
        return {
            "test": "https://ksef-test.mf.gov.pl/api/v2",
            "demo": "https://ksef-demo.mf.gov.pl/api/v2",
        }

    def get_invoice_url(self, ksef_number: str) -> str:
        base = self.base_url.replace("/api/v2", "")
        return f"{base}/invoices/{ksef_number}"
