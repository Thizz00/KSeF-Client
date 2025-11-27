import requests
from typing import Dict, Optional
from ksef.constants import (
    CONTENT_TYPE_JSON,
    ACCEPT_JSON,
    ACCEPT_XML,
    ACCEPT_OCTET_STREAM,
    AUTH_HEADER_PREFIX,
)


class HttpClient:

    def __init__(self, base_url: str):
        self.base_url = base_url

    def post_json(
        self,
        endpoint: str,
        payload: Dict,
        token: Optional[str] = None,
        params: Optional[Dict] = None,
    ) -> requests.Response:
        url = self._build_url(endpoint)
        headers = self._build_json_headers(token)
        return requests.post(url, json=payload, headers=headers, params=params)

    def get_json(
        self, endpoint: str, token: Optional[str] = None, params: Optional[Dict] = None
    ) -> requests.Response:
        url = self._build_url(endpoint)
        headers = self._build_headers(ACCEPT_JSON, token)
        return requests.get(url, headers=headers, params=params)

    def get_xml(self, endpoint: str, token: str) -> requests.Response:
        url = self._build_url(endpoint)
        headers = self._build_headers(ACCEPT_XML, token)
        return requests.get(url, headers=headers)

    def get_octet_stream(self, endpoint: str, token: str) -> requests.Response:
        url = self._build_url(endpoint)
        headers = self._build_headers(ACCEPT_OCTET_STREAM, token)
        return requests.get(url, headers=headers)

    def _build_url(self, endpoint: str) -> str:
        return f"{self.base_url}{endpoint}"

    def _build_json_headers(self, token: Optional[str] = None) -> Dict:
        headers = {"Content-Type": CONTENT_TYPE_JSON, "Accept": ACCEPT_JSON}
        if token:
            headers["Authorization"] = f"{AUTH_HEADER_PREFIX}{token}"
        return headers

    def _build_headers(self, accept: str, token: Optional[str] = None) -> Dict:
        headers = {"Accept": accept}
        if token:
            headers["Authorization"] = f"{AUTH_HEADER_PREFIX}{token}"
        return headers
