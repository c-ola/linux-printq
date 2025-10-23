#!/usr/bin/env python3
import argparse
import getpass
from base64 import b64encode
from typing import Any, Optional
import requests
import subprocess


def make_auth_header(username: str, password: str) -> dict:
    """Return a Basic Auth header dict."""
    auth_str = f"{username}:{password}"
    b64 = b64encode(auth_str.encode()).decode()
    return {"Authorization": f"Basic {b64}"}


def fetch_json(session: requests.Session, url: str, verify=False) -> Optional[Any]:
    """Fetch list from /printers or /servers endpoint."""
    try:
        r = session.get(url, timeout=5, verify=verify)
        r.raise_for_status()
        if r.headers.get("content-type", "").startswith("application/json"):
            return r.json()
        return None
    except Exception as e:
        print(f"❌ Failed to fetch {url}: {e}")
        exit()


def main():
    parser = argparse.ArgumentParser(
        description="A CLI tool for adding printq printers to CUPS on linux."
    )
    parser.add_argument("--host", help="host (i.e. libraryprintq.printq.queensu.ca)", default="libraryprintq.printq.queensu.ca")
    parser.add_argument("--printer", help="Printer name (if omitted, checks selected server for printers)")
    #parser.add_argument("--server", help="server url for the printer (if ommitted, searches for available servers on host), use with --port")
    parser.add_argument("--port", help="Port for the printer server (default: 9164)", default=9164)
    parser.add_argument("--locale", default="en-US", help="Locale parameter")
    parser.add_argument("--scheme-https", action="store_true", help="Add &scheme=https param")
    parser.add_argument("--insecure", action="store_true", help="Ignore SSL certificate errors")

    args = parser.parse_args()
    verify_tls = not args.insecure
    session = requests.Session()

    printer = args.printer
    if printer is None:
        print("Available printers:")
        printers = fetch_json(session, f"https://{args.host}:{args.port}/printers", verify=False)
        if printers is not None:
            for i, p in enumerate(printers, 1):
                name = p["name"]
                print(f'\t{i}. {name}')
            choice = input("Select printer number: ").strip()
            printer = printers[int(choice) - 1]
            printer_name = printer["name"]
        else:
            print("Failed to select printer")
            exit()
    else:
        printer_name = args.printer

    username = input("Username: ")
    password = getpass.getpass("Password: ")

    session.headers.update(make_auth_header(username, password))

    req = f"printerName={printer_name}&serverName={args.host}&locale={args.locale}"
    if args.scheme_https:
        req += "&scheme=https"

    printer_url_req = f"https://{args.host}:{args.port}/printer-url?{req}"

    print(f"\n📡 Sending request to {printer_url_req}")

    try:
        response = session.get(printer_url_req, verify=False)
        print(f"\nStatus: {response.status_code}")
        if response.status_code == 200:
            print("Adding printer:", printer_name)
            print_cmd = f"lpadmin -p {printer_name} -E -v \"{response.text}\""
            res = subprocess.run(["lpadmin", "-p", printer_name, "-E", "-v", response.text], capture_output=True, text=True)
            if res.returncode == 0:
                print("Successfully added printer. Check http://localhost:631/printers/ to see if it.")
            else:
                print("Adding printer to cups failed")
        else:
            print("Failed to get printer url")
    except Exception as e:
        print(f"Request failed: {e}")
        exit()


if __name__ == "__main__":
    main()

