#!/usr/bin/env python3
import argparse
import getpass
import sys
from base64 import b64encode
from typing import Any, Dict, Optional
import requests


def make_auth_header(username: str, password: str) -> dict:
    """Return a Basic Auth header dict."""
    auth_str = f"{username}:{password}"
    b64 = b64encode(auth_str.encode()).decode()
    return {"Authorization": f"Basic {b64}"}


def fetch_list(session: requests.Session, url: str) -> Optional[Any]:
    """Fetch list from /printers or /servers endpoint."""
    try:
        r = session.get(url, timeout=5, verify=False)
        r.raise_for_status()
        if r.headers.get("content-type", "").startswith("application/json"):
            return r.json()
        return None
    except Exception as e:
        sys.exit(f"❌ Failed to fetch {url}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Send authenticated printer request with server and printer selection."
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

    # Prepare session
    session = requests.Session()
    """if args.server is None:
        host = args.host.rstrip('/')
        url = f"https://{host}:{args.port}"
        servers = fetch_list(session, f"{url}/servers")
        if servers := servers:
            print("Available servers:")
            for i, s in enumerate(servers["servers"], 1):
                print(f"\t{i}: {s}")
            choice = input("Select server number:").rstrip()
            server = servers["servers"][int(choice) - 1]
        else:
            print("Using host for servers")
            server = f"https://{host}:{args.port}"
    else:
        server = f"{args.server.rstrip('/')}:{args.port}"
        host = args.server.split('//')[0].rstrip('-1')
    
    print(f"Using server: {server}")
    """


    printer = args.printer
    if printer is None:
        print("Available printers:")
        printers = fetch_list(session, f"https://{args.host}:{args.port}/printers")
        if printers is not None:
            for i, p in enumerate(printers, 1):
                name = p["name"]
                print(f'\t{i}. {name}')
            choice = input("Select printer number: ").strip()
            printer = printers[int(choice) - 1]["name"]
        else:
            print("Failed to select printer")
            exit()


    username = input("Please enter your username:")
    password = getpass.getpass("Password")

    session.headers.update(make_auth_header(username, password))

    # Build request data
    data = f"printerName={printer}&serverName={args.host}&locale={args.locale}"
    if args.scheme_https:
        data += "&scheme=https"

    printer_url = f"https://{args.host}:{args.port}/printer-url?{data}"

    print(f"\n📡 Sending request to {printer_url}")

    try:
        response = session.get(printer_url, verify=False)
        print(f"\nStatus: {response.status_code}")
        print(response.text)
    except Exception as e:
        sys.exit(f"❌ Request failed: {e}")


if __name__ == "__main__":
    main()

