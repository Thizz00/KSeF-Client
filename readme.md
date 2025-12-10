# KSeF Client - Obsługa Krajowego Systemu e-Faktur - Środowisko testowe/przedprodukcyjne

Projekt do komunikacji z API Krajowego Systemu e-Faktur (KSeF) umożliwiająca wysyłkę, pobieranie i wyszukiwanie faktur elektronicznych.

## Wymagania

- Konto w systemie KSeF - testowe/przedprodukcyjne
- Token autoryzacyjny KSeF
- NIP podmiotu

## Instalacja
```bash
pip install -r requirements.txt
```

## Konfiguracja

Utwórz plik `.env`:
```env
KSEF_NIP=twoj_nip
KSEF_TOKEN=twoj_token_ksef
KSEF_ENV=test/demo
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
python main.py search-download --date-from 2025-11-01 --date-to 2025-11-30
python main.py download-single KSEF_NUMBER
```

Podczas wyszukiwania faktur na podstawie określonych interwałów dat, kluczowe jest ustawienie parametru **`subject_type`**. Definiuje on, jakiego rodzaju faktury mają zostać pobrane, bazując na roli podmiotu.

| Wartość `subject_type` | Opis |
| :--- | :--- |
| **`Subject1`** | **Faktury Sprzedażowe** (wystawione przez Podmiot 1) |
| **`Subject2`** | **Faktury Zakupowe** (wystawione dla Podmiot 2) |
| **`Subject3`** | **Faktury Podmiotu Innego** (np. podmiotu trzeciego) |
| **`SubjectAuthorized`** | **Faktury Podmiotu Upoważnionego** |

```bash
-- main.py

invoices = search_invoices_from_ksef(
        client=client,
        subject_type="Subject1", <-- parametr do ustawienia
        date_type="PermanentStorage",
        date_from=date_from_ksef,
        date_to=date_to_ksef,
        page_size=100,
        sort_order="Desc",
    )
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
