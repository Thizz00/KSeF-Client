# KSeF Client - testy obsługi Krajowego Systemu e-Faktur - Środowisko testowe

Projekt do komunikacji z API Krajowego Systemu e-Faktur (KSeF) umożliwiająca wysyłkę, pobieranie i wyszukiwanie faktur elektronicznych.

## Wymagania

- Konto w systemie KSeF testowe
- Token autoryzacyjny KSeF
- NIP podmiotu

## Instalacja
```bash
pip install -r requirements.txt
```

## Konfiguracja

Utwórz plik `.env`:
```env
KSEF_NIP=1234567890
KSEF_TOKEN=twoj_token_ksef
KSEF_ENV=test
KSEF_RATE_LIMIT=10
```

## Użycie CLI

### Wysyłka faktury
```bash
python main.py send-single invoice.xml
python main.py send-batch --directory invoices_directory
```

### Pobieranie faktur
```bash
python main.py search-download --date-from 2025-11-01T00:00:00.000+00:00 --date-to 2025-11-30T23:59:59.999+00:00
python main.py download-single KSEF_NUMBER
```


## Architektura

Biblioteka składa się z następujących komponentów:

- **KSeFClient** - główna fasada dla wszystkich operacji
- **AuthService** - autoryzacja z wykorzystaniem tokenów
- **SessionService** - zarządzanie sesjami online
- **InvoiceService** - wysyłka, pobieranie, wyszukiwanie faktur
- **EncryptionManager** - szyfrowanie AES-256 i RSA-OAEP
- **RateLimiter** - kontrola częstotliwości żądań


## Licencja

Projekt dla celów testowych dla integracji z systemem KSeF Ministerstwa Finansów.