import argparse
from dotenv import load_dotenv

load_dotenv()

from ksef.config import KSeFConfig
from ksef.client import KSeFClient
from ksef.operations import (
    send_xml_from_file,
    send_xmls_from_directory,
    download_invoice,
    search_invoices_from_ksef,
)


def search_and_download(client: KSeFClient, date_from: str, date_to: str):

    print(f"Searching invoices from {date_from} to {date_to}...")

    invoices = search_invoices_from_ksef(
        client=client,
        subject_type="Subject1",
        date_type="PermanentStorage",
        date_from=date_from,
        date_to=date_to,
        page_size=20,
        sort_order="Desc",
    )

    if not invoices or not invoices.get("invoices"):
        print("No invoices found")
        return

    ksef_numbers = [inv["ksefNumber"] for inv in invoices["invoices"]]
    print(f"Found {len(ksef_numbers)} invoices. Starting download...")

    client.download_multiple_invoices(ksef_numbers)
    print("Download of found invoices completed.")


def send_single(client: KSeFClient, xml_path: str):
    result = send_xml_from_file(client, xml_path)

    if result and result.get("status") == "accepted":
        print(f"Invoice sent: {result['ksefNumber']}")
        print(f"Link: {result['link']}")
    else:
        print(
            f"Failed: {result.get('description', 'Unknown error') if result else 'Send error'}"
        )


def send_batch(client: KSeFClient, directory: str):
    send_xmls_from_directory(client, directory)


def download_single(client: KSeFClient, ksef_number: str):
    success, path = download_invoice(client, ksef_number)
    print(f"Downloaded: {path}" if success else "Download failed")


def main():
    parser = argparse.ArgumentParser(
        description="Command Line Interface (CLI) tool for KSeF.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Available operations"
    )

    parser_send_single = subparsers.add_parser(
        "send-single", help="Send a single XML file."
    )
    parser_send_single.add_argument(
        "xml_path", type=str, help="Path to the XML invoice file."
    )

    parser_send_batch = subparsers.add_parser(
        "send-batch", help="Send all XML files from a directory."
    )
    parser_send_batch.add_argument(
        "--directory", type=str, help=f"Directory containing XML files to send."
    )

    parser_search_download = subparsers.add_parser(
        "search-download",
        help="Search for and download invoices within a specified date range.",
    )
    parser_search_download.add_argument(
        "--date-from",
        type=str,
        default="2025-11-01T00:00:00.000+00:00",
        help="Start date for the search (e.g., 2025-11-01T00:00:00.000+00:00).",
    )
    parser_search_download.add_argument(
        "--date-to",
        type=str,
        default="2025-11-30T23:59:59.999+00:00",
        help="End date for the search (e.g., 2025-11-30T23:59:59.999+00:00).",
    )

    parser_download_single = subparsers.add_parser(
        "download-single", help="Download a single invoice using its KSeF number."
    )
    parser_download_single.add_argument(
        "ksef_number", type=str, help="The KSeF number of the invoice to download."
    )

    args = parser.parse_args()

    client = KSeFClient(KSeFConfig())

    if not client.authenticate():
        print("Error: Authentication failed")
        return

    print("Authentication successful")

    if args.command == "send-single":
        send_single(client, args.xml_path)
    elif args.command == "send-batch":
        send_batch(client, args.directory)
    elif args.command == "search-download":
        search_and_download(client, args.date_from, args.date_to)
    elif args.command == "download-single":
        download_single(client, args.ksef_number)


if __name__ == "__main__":
    main()
