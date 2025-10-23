#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject
from base64 import b64encode
import requests
import subprocess


"""
The UI stuff here is vibecoded because yea.
Otherstuff is half vibecoded, but I basically had to redo the whole 
fetching/adding printers because what chatGPT gave was bad.
"""

def make_auth_header(username: str, password: str) -> dict:
    auth_str = f"{username}:{password}"
    b64 = b64encode(auth_str.encode()).decode()
    return {"Authorization": f"Basic {b64}"}

def fetch_json(session: requests.Session, url: str, verify=True):
    try:
        r = session.get(url, timeout=5, verify=verify)
        r.raise_for_status()
        if r.headers.get("content-type", "").startswith("application/json"):
            return r.json()
        return None
    except Exception as e:
        return f"Failed to fetch {url}: {e}"

class PrinterUI(Gtk.Window):
    def __init__(self):
        super().__init__(title="Printer Setup")
        self.set_border_width(10)
        self.set_default_size(400, 350)

        grid = Gtk.Grid(column_spacing=10, row_spacing=10)
        self.add(grid)

        # Host
        grid.attach(Gtk.Label(label="Host:"), 0, 0, 1, 1)
        self.host_entry = Gtk.Entry()
        self.host_entry.set_text("libraryprintq.printq.queensu.ca")
        grid.attach(self.host_entry, 1, 0, 2, 1)

        # Port
        grid.attach(Gtk.Label(label="Port:"), 0, 1, 1, 1)
        self.port_entry = Gtk.Entry()
        self.port_entry.set_text("9164")
        grid.attach(self.port_entry, 1, 1, 2, 1)

        # Username
        grid.attach(Gtk.Label(label="Username:"), 0, 2, 1, 1)
        self.user_entry = Gtk.Entry()
        grid.attach(self.user_entry, 1, 2, 2, 1)

        # Password
        grid.attach(Gtk.Label(label="Password:"), 0, 3, 1, 1)
        self.pass_entry = Gtk.Entry()
        self.pass_entry.set_visibility(False)
        grid.attach(self.pass_entry, 1, 3, 2, 1)

        # HTTPS checkbox
        self.https_check = Gtk.CheckButton(label="Use HTTPS scheme")
        grid.attach(self.https_check, 0, 4, 3, 1)

        # Insecure checkbox
        self.insecure_check = Gtk.CheckButton(label="Ignore SSL errors")
        self.insecure_check.set_active(True)
        grid.attach(self.insecure_check, 0, 5, 3, 1)

        # Fetch printers button
        self.fetch_list_btn = Gtk.Button(label="Fetch Printers")
        self.fetch_list_btn.connect("clicked", self.on_fetch_printers)
        grid.attach(self.fetch_list_btn, 0, 6, 3, 1)

        # Printer selection ComboBox
        grid.attach(Gtk.Label(label="Printer:"), 0, 7, 1, 1)
        self.printer_combo = Gtk.ComboBoxText()
        grid.attach(self.printer_combo, 1, 7, 2, 1)

        # Add printer button
        self.add_btn = Gtk.Button(label="Add Printer")
        self.add_btn.connect("clicked", self.on_add_printer)
        grid.attach(self.add_btn, 0, 8, 3, 1)

        # Output area
        self.output = Gtk.TextView()
        self.output.set_editable(False)
        self.output.set_cursor_visible(False)
        scroll = Gtk.ScrolledWindow()
        scroll.set_hexpand(True)
        scroll.set_vexpand(True)
        scroll.add(self.output)
        grid.attach(scroll, 0, 9, 3, 3)

    def append_output(self, text: str):
        buffer = self.output.get_buffer()
        buffer.insert(buffer.get_end_iter(), text + "\n")

    def on_fetch_printers(self, widget):
        host = self.host_entry.get_text()
        port = self.port_entry.get_text()
        insecure = self.insecure_check.get_active()
        verify_tls = not insecure

        session = requests.Session()

        url = f"https://{host}:{port}/printers"
        self.append_output(f"Fetching printers from {url}")
        result = fetch_json(session, url, verify=verify_tls)
        if isinstance(result, str):
            self.append_output(f"❌ {result}")
            return

        self.printer_combo.remove_all()
        for printer in result:
            self.printer_combo.append_text(printer["name"])
        self.append_output(f"✅ Fetched {len(result)} printers")

    def on_add_printer(self, widget):
        host = self.host_entry.get_text()
        port = self.port_entry.get_text()
        printer_name = self.printer_combo.get_active_text()
        username = self.user_entry.get_text()
        password = self.pass_entry.get_text()
        scheme_https = self.https_check.get_active()
        insecure = self.insecure_check.get_active()
        verify_tls = not insecure

        if not printer_name:
            self.append_output("❌ Select a printer first")
            return

        username = self.user_entry.get_text()
        password = self.pass_entry.get_text()
        if not username or not password:
            self.append_output("❌ Enter username and password to add a printer")
            return
        
        session = requests.Session()
        session.headers.update(make_auth_header(username, password))

        req = f"printerName={printer_name}&serverName={host}&locale=en-US"
        if scheme_https:
            req += "&scheme=https"

        printer_url_req = f"https://{host}:{port}/printer-url?{req}"
        self.append_output(f"Sending request to {printer_url_req}")

        try:
            response = session.get(printer_url_req, verify=verify_tls)
            self.append_output(f"Status: {response.status_code}")
            if response.status_code == 200:
                self.append_output(f"Adding printer: {printer_name}")
                res = subprocess.run(
                    ["lpadmin", "-p", printer_name, "-E", "-v", response.text],
                    capture_output=True, text=True
                )
                if res.returncode == 0:
                    self.append_output("Successfully added printer!")
                else:
                    self.append_output(f"Adding printer failed {res.returncode}:\n" + res.stderr)
            else:
                self.append_output("Failed to get printer URL")
        except Exception as e:
            self.append_output(f"Request failed: {e}")

if __name__ == "__main__":
    win = PrinterUI()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

