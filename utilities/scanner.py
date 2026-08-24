#!/usr/bin/env python3

import ipaddress
import platform
import re
import socket
import struct
import subprocess
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


# ============================================================
# CONFIGURAZIONE INTERNA
# L'utente NON deve modificare nulla
# ============================================================

TIMEOUT = 0.5
MAX_WORKERS = 100

TARGET_KEY = "program_name"
TARGET_VALUE = "in-out"


# ============================================================
# RILEVAMENTO RETE
# ============================================================

def get_local_ip():
    """
    Determina l'IP dell'interfaccia di rete principale.
    Non viene effettuata realmente una connessione a Internet.
    """

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    finally:
        sock.close()


def get_netmask(local_ip):
    """
    Recupera la netmask dell'interfaccia che possiede local_ip.
    """

    system = platform.system()

    if system == "Windows":
        return get_netmask_windows(local_ip)

    if system == "Linux":
        return get_netmask_linux(local_ip)

    # Fallback
    return "255.255.255.0"


def get_netmask_windows(local_ip):

    try:
        output = subprocess.check_output(
            ["ipconfig"],
            text=True,
            encoding="utf-8",
            errors="ignore"
        )

        lines = output.splitlines()

        for i, line in enumerate(lines):

            if local_ip not in line:
                continue

            # Cerca la netmask nelle righe successive
            for next_line in lines[i + 1:i + 8]:

                match = re.search(
                    r"(\d{1,3}(?:\.\d{1,3}){3})",
                    next_line
                )

                if not match:
                    continue

                value = match.group(1)

                # Una subnet mask valida contiene tipicamente
                # 255, 254, 252, 248, 240, 224, 192, 128 o 0
                try:
                    mask = ipaddress.IPv4Address(value)

                    if str(mask) != local_ip:
                        return str(mask)

                except ValueError:
                    continue

    except Exception:
        pass

    return "255.255.255.0"


def get_netmask_linux(local_ip):

    try:
        import fcntl

        interfaces = socket.if_nameindex()

        for _, interface in interfaces:

            sock = socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM
            )

            try:

                interface_bytes = interface.encode("utf-8")[:15]

                request = struct.pack(
                    "256s",
                    interface_bytes
                )

                # SIOCGIFADDR
                result = fcntl.ioctl(
                    sock.fileno(),
                    0x8915,
                    request
                )

                ip = socket.inet_ntoa(
                    result[20:24]
                )

                if ip != local_ip:
                    continue

                # SIOCGIFNETMASK
                result = fcntl.ioctl(
                    sock.fileno(),
                    0x891b,
                    request
                )

                return socket.inet_ntoa(
                    result[20:24]
                )

            except Exception:
                pass

            finally:
                sock.close()

    except Exception:
        pass

    return "255.255.255.0"


def get_own_network():

    local_ip = get_local_ip()
    netmask = get_netmask(local_ip)

    return ipaddress.IPv4Network(
        f"{local_ip}/{netmask}",
        strict=False
    )


# ============================================================
# CONTROLLO HOST
# ============================================================

def check_host(ip, stop_event):

    if stop_event.is_set():
        return None

    url = f"http://{ip}/whoami"

    try:

        response = requests.get(
            url,
            timeout=TIMEOUT,
            headers={
                "Connection": "close"
            }
        )

        if response.status_code != 200:
            return None

        data = response.json()

        if (
            isinstance(data, dict)
            and data.get(TARGET_KEY) == TARGET_VALUE
        ):
            return ip

    except (
        requests.RequestException,
        ValueError,
        TypeError,
        OSError
    ):
        pass

    return None


# ============================================================
# GUI
# ============================================================

class InOutScanner(tk.Tk):

    def __init__(self):

        super().__init__()

        self.title("IN-OUT Scanner")

        self.geometry("650x500")
        self.minsize(550, 400)

        self.stop_event = threading.Event()
        self.scanning = False
        self.executor = None

        self.network = None
        self.found = []

        self.create_interface()

        # Rilevamento automatico della rete
        threading.Thread(
            target=self.detect_network,
            daemon=True
        ).start()

    # --------------------------------------------------------
    # INTERFACCIA
    # --------------------------------------------------------

    def create_interface(self):

        # Titolo
        title = ttk.Label(
            self,
            text="IN-OUT Scanner",
            font=("TkDefaultFont", 20, "bold")
        )

        title.pack(pady=(20, 5))

        subtitle = ttk.Label(
            self,
            text="Ricerca automatica dei dispositivi IN-OUT"
        )

        subtitle.pack(pady=(0, 15))

        # Informazioni rete
        network_frame = ttk.Frame(self)

        network_frame.pack(
            fill="x",
            padx=30
        )

        ttk.Label(
            network_frame,
            text="Rete:"
        ).pack(side="left")

        self.network_label = ttk.Label(
            network_frame,
            text="Rilevamento..."
        )

        self.network_label.pack(
            side="left",
            padx=8
        )

        # Pulsanti
        button_frame = ttk.Frame(self)

        button_frame.pack(
            pady=20
        )

        self.start_button = ttk.Button(
            button_frame,
            text="AVVIA SCANSIONE",
            command=self.start_scan
        )

        self.start_button.pack(
            side="left",
            padx=8,
            ipadx=20,
            ipady=5
        )

        self.stop_button = ttk.Button(
            button_frame,
            text="STOP",
            command=self.stop_scan,
            state="disabled"
        )

        self.stop_button.pack(
            side="left",
            padx=8,
            ipadx=20,
            ipady=5
        )

        # Progress bar
        self.progress = ttk.Progressbar(
            self,
            maximum=100
        )

        self.progress.pack(
            fill="x",
            padx=30
        )

        # Stato
        self.status_label = ttk.Label(
            self,
            text="Pronto"
        )

        self.status_label.pack(
            pady=8
        )

        # Risultati
        results_frame = ttk.LabelFrame(
            self,
            text="Dispositivi IN-OUT trovati"
        )

        results_frame.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=(10, 10)
        )

        scrollbar = ttk.Scrollbar(
            results_frame,
            orient="vertical"
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.results = tk.Listbox(
            results_frame,
            font=("TkFixedFont", 11),
            yscrollcommand=scrollbar.set
        )

        self.results.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )

        scrollbar.config(
            command=self.results.yview
        )

        # Doppio click sull'IP
        self.results.bind(
            "<Double-Button-1>",
            self.open_selected
        )

        # Contatore
        self.count_label = ttk.Label(
            self,
            text="Dispositivi trovati: 0"
        )

        self.count_label.pack(
            pady=(0, 15)
        )

    # --------------------------------------------------------
    # RILEVAMENTO RETE
    # --------------------------------------------------------

    def detect_network(self):

        try:

            network = get_own_network()

            self.network = network

            self.after(
                0,
                lambda: self.network_label.config(
                    text=str(network)
                )
            )

            self.after(
                0,
                lambda: self.status_label.config(
                    text="Pronto per la scansione"
                )
            )

        except Exception as error:

            self.after(
                0,
                lambda: self.network_label.config(
                    text="Rete non rilevata"
                )
            )

            self.after(
                0,
                lambda: self.status_label.config(
                    text="Errore nel rilevamento della rete"
                )
            )

            self.after(
                0,
                lambda: messagebox.showerror(
                    "Errore",
                    f"Impossibile rilevare la rete:\n\n{error}"
                )
            )

    # --------------------------------------------------------
    # START
    # --------------------------------------------------------

    def start_scan(self):

        if self.scanning:
            return

        if self.network is None:

            messagebox.showwarning(
                "Attendere",
                "Attendere il rilevamento della rete."
            )

            return

        self.scanning = True

        self.stop_event.clear()

        self.found.clear()

        self.results.delete(
            0,
            tk.END
        )

        self.progress["value"] = 0

        self.count_label.config(
            text="Dispositivi trovati: 0"
        )

        self.start_button.config(
            state="disabled"
        )

        self.stop_button.config(
            state="normal"
        )

        threading.Thread(
            target=self.scan_network,
            daemon=True
        ).start()

    # --------------------------------------------------------
    # STOP
    # --------------------------------------------------------

    def stop_scan(self):

        if not self.scanning:
            return

        self.stop_event.set()

        self.stop_button.config(
            state="disabled"
        )

        self.status_label.config(
            text="Arresto scansione..."
        )

    # --------------------------------------------------------
    # SCANSIONE
    # --------------------------------------------------------

    def scan_network(self):

        hosts = list(
            self.network.hosts()
        )

        total = len(hosts)

        completed = 0

        self.after(
            0,
            lambda: self.status_label.config(
                text=f"Scansione di {total} dispositivi..."
            )
        )

        try:

            self.executor = ThreadPoolExecutor(
                max_workers=MAX_WORKERS
            )

            futures = {}

            for ip in hosts:

                if self.stop_event.is_set():
                    break

                future = self.executor.submit(
                    check_host,
                    str(ip),
                    self.stop_event
                )

                futures[future] = str(ip)

            for future in as_completed(futures):

                completed += 1

                if self.stop_event.is_set():
                    break

                try:

                    result = future.result()

                    if result:

                        self.found.append(result)

                        self.after(
                            0,
                            lambda ip=result:
                            self.add_result(ip)
                        )

                except Exception:
                    pass

                percentage = (
                    completed / total * 100
                    if total
                    else 100
                )

                self.after(
                    0,
                    lambda p=percentage, c=completed:
                    self.update_progress(p, c, total)
                )

        finally:

            if self.executor:

                self.executor.shutdown(
                    wait=False,
                    cancel_futures=True
                )

                self.executor = None

            stopped = self.stop_event.is_set()

            self.after(
                0,
                lambda: self.scan_finished(stopped)
            )

    # --------------------------------------------------------
    # RISULTATO
    # --------------------------------------------------------

    def add_result(self, ip):

        self.results.insert(
            tk.END,
            ip
        )

        self.results.see(
            tk.END
        )

        count = self.results.size()

        self.count_label.config(
            text=f"Dispositivi trovati: {count}"
        )

    # --------------------------------------------------------
    # PROGRESS
    # --------------------------------------------------------

    def update_progress(
        self,
        percentage,
        completed,
        total
    ):

        self.progress["value"] = percentage

        self.status_label.config(
            text=f"Scansione: {completed}/{total}"
        )

    # --------------------------------------------------------
    # FINE SCANSIONE
    # --------------------------------------------------------

    def scan_finished(self, stopped):

        self.scanning = False

        self.start_button.config(
            state="normal"
        )

        self.stop_button.config(
            state="disabled"
        )

        count = len(self.found)

        if stopped:

            self.status_label.config(
                text=f"Scansione interrotta - trovati: {count}"
            )

        else:

            self.progress["value"] = 100

            self.status_label.config(
                text=f"Scansione completata - trovati: {count}"
            )

    # --------------------------------------------------------
    # APRI /WHOAMI
    # --------------------------------------------------------

    def open_selected(self, event=None):

        selection = self.results.curselection()

        if not selection:
            return

        ip = self.results.get(
            selection[0]
        )

        webbrowser.open(
            f"http://{ip}/whoami"
        )


# ============================================================
# AVVIO
# ============================================================

if __name__ == "__main__":

    app = InOutScanner()

    app.mainloop()