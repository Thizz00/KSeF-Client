# HTTP Status Codes
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_ACCEPTED = 202
HTTP_NO_CONTENT = 204
HTTP_BAD_REQUEST = 400
HTTP_METHOD_NOT_ALLOWED = 405

# Processing Status Codes
STATUS_ACCEPTED = 200
STATUS_PROCESSING = 100
STATUS_PROCESSING_EXTENDED = 150
STATUS_ERROR_THRESHOLD = 400

# Authentication
AUTH_HEADER_PREFIX = "Bearer "
CONTENT_TYPE_JSON = "application/json"
CONTENT_TYPE_XML = "application/xml"
ACCEPT_JSON = "application/json"
ACCEPT_XML = "application/xml"
ACCEPT_OCTET_STREAM = "application/octet-stream"

# Encryption
AES_KEY_SIZE = 32  # AES-256
AES_BLOCK_SIZE = 16
AES_MODE_BITS = 128
PKCS7_BLOCK_SIZE = 128

# API Endpoints
ENDPOINT_AUTH_CHALLENGE = "/auth/challenge"
ENDPOINT_AUTH_KSEF_TOKEN = "/auth/ksef-token"
ENDPOINT_AUTH_STATUS = "/auth/{reference}"
ENDPOINT_AUTH_REDEEM = "/auth/token/redeem"
ENDPOINT_PUBLIC_KEYS = "/security/public-key-certificates"
ENDPOINT_SESSION_ONLINE = "/sessions/online"
ENDPOINT_SESSION_INVOICES = "/sessions/online/{session}/invoices"
ENDPOINT_SESSION_INVOICE_LIST = "/sessions/{session}/invoices"
ENDPOINT_SESSION_CLOSE = "/sessions/online/{session}/close"
ENDPOINT_INVOICE_XML = "/invoices/ksef/{number}"
ENDPOINT_INVOICE_METADATA = "/invoices/metadata/{number}"
ENDPOINT_INVOICE_SEARCH = "/invoices/query/metadata"

# Certificate Types
CERT_TYPE_ENCRYPTION = "encryption"
CERT_USAGE_SYMMETRIC_KEY = "SymmetricKeyEncryption"

# Context Identifier
CONTEXT_TYPE_NIP = "nip"

# Form Code
FORM_SYSTEM_CODE = "FA (3)"
FORM_SCHEMA_VERSION = "1-0E"
FORM_VALUE = "FA"

# Polling
DEFAULT_MAX_ATTEMPTS = 30
DEFAULT_DELAY_SECONDS = 1
EXTENDED_MAX_ATTEMPTS = 60
EXTENDED_DELAY_SECONDS = 2
AUTH_WAIT_SECONDS = 1

# Rate Limiting
DEFAULT_RATE_LIMIT = 10
RATE_LIMIT_WINDOW = 1.0

# File Operations
DEFAULT_ENCODING = "utf-8"
DEFAULT_FILE_PATTERN = "*.xml"
DEFAULT_LOG_DIR = "logs"
DEFAULT_DOWNLOAD_DIR = "downloaded_invoices_ksef"
DEFAULT_SEND_DIR = "invoices_to_send_ksef"

# Logging
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
LOG_FORMAT_CONSOLE = "%(message)s"
