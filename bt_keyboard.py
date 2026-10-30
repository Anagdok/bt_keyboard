import os
import sys
import time
import socket
import subprocess
import threading
import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib
import tkinter as tk
from tkinter import ttk, messagebox

# ==============================================================================
# 1. MAPOWANIE ZNAKÓW NA KODY HID (Z OBSŁUGĄ POLSKICH ZNAKÓW)
# ==============================================================================
# Modyfikatory HID:
# 0x00 = Brak, 0x02 = Lewy Shift, 0x40 = Prawy Alt (AltGr), 0x42 = Shift + AltGr
CHAR_TO_HID = {
    'a': (0x00, 0x04), 'b': (0x00, 0x05), 'c': (0x00, 0x06), 'd': (0x00, 0x07),
    'e': (0x00, 0x08), 'f': (0x00, 0x09), 'g': (0x00, 0x0a), 'h': (0x00, 0x0b),
    'i': (0x00, 0x0c), 'j': (0x00, 0x0d), 'k': (0x00, 0x0e), 'l': (0x00, 0x0f),
    'm': (0x00, 0x10), 'n': (0x00, 0x11), 'o': (0x00, 0x12), 'p': (0x00, 0x13),
    'q': (0x00, 0x14), 'r': (0x00, 0x15), 's': (0x00, 0x16), 't': (0x00, 0x17),
    'u': (0x00, 0x18), 'v': (0x00, 0x19), 'w': (0x00, 0x1a), 'x': (0x00, 0x1b),
    'y': (0x00, 0x1c), 'z': (0x00, 0x1d),

    'A': (0x02, 0x04), 'B': (0x02, 0x05), 'C': (0x02, 0x06), 'D': (0x02, 0x07),
    'E': (0x02, 0x08), 'F': (0x02, 0x09), 'G': (0x02, 0x0a), 'H': (0x02, 0x0b),
    'I': (0x02, 0x0c), 'J': (0x02, 0x0d), 'K': (0x02, 0x0e), 'L': (0x02, 0x0f),
    'M': (0x02, 0x10), 'N': (0x02, 0x11), 'O': (0x02, 0x12), 'P': (0x02, 0x13),
    'Q': (0x02, 0x14), 'R': (0x02, 0x15), 'S': (0x02, 0x16), 'T': (0x02, 0x17),
    'U': (0x02, 0x18), 'V': (0x02, 0x19), 'W': (0x02, 0x1a), 'X': (0x02, 0x1b),
    'Y': (0x02, 0x1c), 'Z': (0x02, 0x1d),

    # Polskie znaki (AltGr + litera)
    'ą': (0x40, 0x04), 'ć': (0x40, 0x06), 'ę': (0x40, 0x08), 'ł': (0x40, 0x0f),
    'ń': (0x40, 0x11), 'ó': (0x40, 0x12), 'ś': (0x40, 0x16), 'ź': (0x40, 0x1b),
    'ż': (0x40, 0x1d),
    'Ą': (0x42, 0x04), 'Ć': (0x42, 0x06), 'Ę': (0x42, 0x08), 'Ł': (0x42, 0x0f),
    'Ń': (0x42, 0x11), 'Ó': (0x42, 0x12), 'Ś': (0x42, 0x16), 'Ź': (0x42, 0x1b),
    'Ż': (0x42, 0x1d),

    '1': (0x00, 0x1e), '2': (0x00, 0x1f), '3': (0x00, 0x20), '4': (0x00, 0x21),
    '5': (0x00, 0x22), '6': (0x00, 0x23), '7': (0x00, 0x24), '8': (0x00, 0x25),
    '9': (0x00, 0x26), '0': (0x00, 0x27),

    '!': (0x02, 0x1e), '@': (0x02, 0x1f), '#': (0x02, 0x20), '$': (0x02, 0x21),
    '%': (0x02, 0x22), '^': (0x02, 0x23), '&': (0x02, 0x24), '*': (0x02, 0x25),
    '(': (0x02, 0x26), ')': (0x02, 0x27),

    '\n': (0x00, 0x28), '\r': (0x00, 0x28), '\b': (0x00, 0x2a), '\t': (0x00, 0x2b),
    ' ': (0x00, 0x2c), '-': (0x00, 0x2d), '_': (0x02, 0x2d), '=': (0x00, 0x2e),
    '+': (0x02, 0x2e), '[': (0x00, 0x2f), '{': (0x02, 0x2f), ']': (0x00, 0x30),
    '}': (0x02, 0x30), '\\': (0x00, 0x31), '|': (0x02, 0x31), ';': (0x00, 0x33),
    ':': (0x02, 0x33), "'": (0x00, 0x34), '"': (0x02, 0x34), '`': (0x00, 0x35),
    '~': (0x02, 0x35), ',': (0x00, 0x36), '<': (0x02, 0x36), '.': (0x00, 0x37),
    '>': (0x02, 0x37), '/': (0x00, 0x38), '?': (0x02, 0x38)
}

KEYSYM_TO_HID = {
    'Return': 0x28, 'Escape': 0x29, 'BackSpace': 0x2a, 'Tab': 0x2b,
    'space': 0x2c, 'Delete': 0x4c, 'Right': 0x4f, 'Left': 0x50,
    'Down': 0x51, 'Up': 0x52,
    'F1': 0x3a, 'F2': 0x3b, 'F3': 0x3c, 'F4': 0x3d, 'F5': 0x3e,
    'F6': 0x3f, 'F7': 0x40, 'F8': 0x41, 'F9': 0x42, 'F10': 0x43,
    'F11': 0x44
}

# ==============================================================================
# 2. REKORD SDP DLA KLAWIATURY BLUETOOTH HID
# ==============================================================================
SDP_RECORD = """
<?xml version="1.0" encoding="UTF-8" ?>
<record>
    <attribute id="0x0001"><sequence><uuid value="0x1124" /></sequence></attribute>
    <attribute id="0x0004">
        <sequence>
            <sequence><uuid value="0x0100" /><uint16 value="0x0011" /></sequence>
            <sequence><uuid value="0x0011" /></sequence>
        </sequence>
    </attribute>
    <attribute id="0x0005"><sequence><uuid value="0x1002" /></sequence></attribute>
    <attribute id="0x0006">
        <sequence>
            <uint16 value="0x656e" /><uint16 value="0x006a" /><uint16 value="0x0100" />
        </sequence>
    </attribute>
    <attribute id="0x0009">
        <sequence><sequence><uuid value="0x1124" /><uint16 value="0x0100" /></sequence></sequence>
    </attribute>
    <attribute id="0x000d">
        <sequence>
            <sequence>
                <sequence><uuid value="0x0100" /><uint16 value="0x0013" /></sequence>
                <sequence><uuid value="0x0011" /></sequence>
            </sequence>
        </sequence>
    </attribute>
    <attribute id="0x0100"><text value="Bluetooth Keyboard" /></attribute>
    <attribute id="0x0101"><text value="USB HID Emulated Keyboard" /></attribute>
    <attribute id="0x0102"><text value="BT HID" /></attribute>
    <attribute id="0x0200"><uint16 value="0x0100" /></attribute>
    <attribute id="0x0201"><uint16 value="0x0111" /></attribute>
    <attribute id="0x0202"><uint8 value="0x40" /></attribute>
    <attribute id="0x0203"><uint8 value="0x00" /></attribute>
    <attribute id="0x0204"><boolean value="true" /></attribute>
    <attribute id="0x0205"><boolean value="true" /></attribute>
    <attribute id="0x0206">
        <sequence>
            <sequence>
                <uint8 value="0x22" />
                <text encoding="hex" value="05010906a101850175019508050719e029e715002501810295017508810395057501050819012905910295017503910395067508150026ff000507190029ff8100c0" />
            </sequence>
        </sequence>
    </attribute>
    <attribute id="0x0207">
        <sequence><sequence><uint16 value="0x0409" /><uint16 value="0x0100" /></sequence></sequence>
    </attribute>
    <attribute id="0x020b"><uint16 value="0x0100" /></attribute>
    <attribute id="0x020c"><uint16 value="0x0c80" /></attribute>
    <attribute id="0x020d"><boolean value="false" /></attribute>
    <attribute id="0x020e"><boolean value="true" /></attribute>
</record>
"""

# ==============================================================================
# 3. KLASY D-BUS (PROFIL HID ORAZ AUTOMATYCZNY AGENT PAROWANIA)
# ==============================================================================
class BluezProfile(dbus.service.Object):
    @dbus.service.method("org.bluez.Profile1", in_signature="", out_signature="")
    def Release(self): pass

    @dbus.service.method("org.bluez.Profile1", in_signature="oha{sv}", out_signature="")
    def NewConnection(self, path, fd, properties): pass

    @dbus.service.method("org.bluez.Profile1", in_signature="o", out_signature="")
    def RequestDisconnection(self, path): pass


class AutoAcceptAgent(dbus.service.Object):
    @dbus.service.method("org.bluez.Agent1", in_signature="", out_signature="")
    def Release(self): pass

    @dbus.service.method("org.bluez.Agent1", in_signature="os", out_signature="")
    def AuthorizeService(self, device, uuid): return

    @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="")
    def RequestAuthorization(self, device): return

    @dbus.service.method("org.bluez.Agent1", in_signature="ou", out_signature="")
    def RequestConfirmation(self, device, passkey): return


# ==============================================================================
# 4. SERWER BLUETOOTH L2CAP
# ==============================================================================
class BluetoothHIDServer:
    P_CTRL = 17
    P_INTR = 19

    def __init__(self, status_callback):
        self.status_callback = status_callback
        self.cinterrupt = None
        self.ccontrol = None
        self.connected = False
        self.running = True

    def configure_fedora_adapter(self, bus):
        adapter_props = dbus.Interface(
            bus.get_object("org.bluez", "/org/bluez/hci0"),
            "org.freedesktop.DBus.Properties"
        )
        adapter_props.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(1))
        adapter_props.Set("org.bluez.Adapter1", "Alias", dbus.String("BT-Keyboard"))
        adapter_props.Set("org.bluez.Adapter1", "DiscoverableTimeout", dbus.UInt32(0))
        adapter_props.Set("org.bluez.Adapter1", "Discoverable", dbus.Boolean(1))
        adapter_props.Set("org.bluez.Adapter1", "Pairable", dbus.Boolean(1))

        subprocess.run(["btmgmt", "--index", "0", "class", "5", "64"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def start_server(self):
        try:
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            bus = dbus.SystemBus()

            self.configure_fedora_adapter(bus)

            agent_path = "/fedora/btkb/agent"
            AutoAcceptAgent(bus, agent_path)
            agent_manager = dbus.Interface(bus.get_object("org.bluez", "/org/bluez"), "org.bluez.AgentManager1")
            agent_manager.RegisterAgent(agent_path, "NoInputNoOutput")
            agent_manager.RequestDefaultAgent(agent_path)

            manager = dbus.Interface(bus.get_object("org.bluez", "/org/bluez"), "org.bluez.ProfileManager1")
            profile_path = "/fedora/btkb/profile"
            BluezProfile(bus, profile_path)

            opts = {
                "ServiceRecord": SDP_RECORD,
                "Role": "server",
                "RequireAuthentication": False,
                "RequireAuthorization": False
            }
            manager.RegisterProfile(profile_path, "00001124-0000-1000-8000-00805f9b34fb", opts)

            glib_loop = GLib.MainLoop()
            threading.Thread(target=glib_loop.run, daemon=True).start()

            self.scontrol = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP)
            self.sinterrupt = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP)
            self.scontrol.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sinterrupt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            self.scontrol.bind((socket.BDADDR_ANY, self.P_CTRL))
            self.sinterrupt.bind((socket.BDADDR_ANY, self.P_INTR))

            self.scontrol.listen(1)
            self.sinterrupt.listen(1)

            self.status_callback("Widoczny jako 'BT-Keyboard'. Sparuj z telefonu lub PC!")

            while self.running:
                self.ccontrol, cinfo = self.scontrol.accept()
                self.cinterrupt, cinfo = self.sinterrupt.accept()
                self.connected = True
                self.status_callback(f"Połączono aktywnie z urządzeniem: {cinfo[0]}")

                while self.connected and self.running:
                    try:
                        data = self.ccontrol.recv(64)
                        if not data:
                            break
                    except Exception:
                        break

                self.connected = False
                self.status_callback("Rozłączono. Oczekiwanie na ponowne połączenie...")

        except Exception as e:
            self.status_callback(f"Błąd Bluetooth: {e}")

    def send_hid_report(self, modifier, keycode):
        if not self.connected or not self.cinterrupt:
            return
        packet = bytearray([0xA1, 0x01, modifier, 0x00, keycode, 0x00, 0x00, 0x00, 0x00, 0x00])
        release = bytearray([0xA1, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        try:
            self.cinterrupt.send(packet)
            time.sleep(0.006)
            self.cinterrupt.send(release)
            time.sleep(0.006)
        except Exception as e:
            self.connected = False
            self.status_callback(f"Utracono połączenie: {e}")


# ==============================================================================
# 5. INTERFEJS GRAFICZNY (GUI Z PRZEŁĄCZNIKIEM TOGGLE DLA TRYBU LIVE)
# ==============================================================================
class BTKeyboardGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Bluetooth HID Keyboard")
        self.root.geometry("620x520")

        self.bt_server = BluetoothHIDServer(self.update_status)
        self.is_typing_text = False
        self.live_mode_active = False

        self.build_ui()

        # Globalne bindowanie klawiszy do okna głównego dla trybu Live
        self.root.bind("<KeyPress>", self.on_global_keypress)

        self.server_thread = threading.Thread(target=self.bt_server.start_server, daemon=True)
        self.server_thread.start()

    def build_ui(self):
        # Status Bluetooth
        status_frame = ttk.LabelFrame(self.root, text="Status Połączenia Bluetooth", padding=10)
        status_frame.pack(fill="x", padx=10, pady=5)

        self.status_label = ttk.Label(status_frame, text="Inicjalizacja usługi BlueZ...", foreground="#0055ff", font=("Sans", 10, "bold"))
        self.status_label.pack(anchor="w")

        # Tryb 1: Przełącznik Toggle (Live Input)
        live_frame = ttk.LabelFrame(self.root, text="Tryb 1: Pisanie na żywo (Live Input Toggle)", padding=10)
        live_frame.pack(fill="x", padx=10, pady=5)

        self.live_toggle_btn = tk.Button(
            live_frame,
            text="TRYB LIVE: WYŁĄCZONY (Kliknij lub wciśnij F12, aby włączyć)",
            font=("Sans", 11, "bold"),
            bg="#f8d7da",
            fg="#721c24",
            activebackground="#f5c6cb",
            height=2,
            command=self.toggle_live_mode
        )
        self.live_toggle_btn.pack(fill="x", pady=4)

        self.live_last_key_label = ttk.Label(
            live_frame,
            text="Gdy tryb Live jest włączony, wszystko co piszesz leci prosto na telefon/PC (F12 wyłącza).",
            foreground="#555555"
        )
        self.live_last_key_label.pack(anchor="w")

        # Tryb 2: Wklej i wyślij (Auto-Typer)
        box_frame = ttk.LabelFrame(self.root, text="Tryb 2: Wklej tekst i wyślij jako klawiatura (Auto-Typer)", padding=10)
        box_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.text_box = tk.Text(box_frame, height=10, font=("Monospace", 10))
        self.text_box.pack(fill="both", expand=True, pady=5)
        # Kliknięcie w pole tekstowe automatycznie wyłącza tryb Live, żebyś mógł spokojnie wkleić tekst
        self.text_box.bind("<Button-1>", lambda e: self.disable_live_mode_if_active())

        controls_frame = ttk.Frame(box_frame)
        controls_frame.pack(fill="x")

        ttk.Label(controls_frame, text="Opóźnienie między znakami (ms):").pack(side="left")
        self.delay_var = tk.IntVar(value=15)
        delay_spin = ttk.Spinbox(controls_frame, from_=1, to=500, textvariable=self.delay_var, width=6)
        delay_spin.pack(side="left", padx=5)

        self.send_btn = ttk.Button(controls_frame, text="Wyślij cały tekst", command=self.start_sending_text)
        self.send_btn.pack(side="right", padx=5)

        self.stop_btn = ttk.Button(controls_frame, text="Zatrzymaj", command=self.stop_sending_text, state="disabled")
        self.stop_btn.pack(side="right")

    def update_status(self, message):
        self.root.after(0, lambda: self.status_label.config(text=message))

    def disable_live_mode_if_active(self):
        if self.live_mode_active:
            self.toggle_live_mode()

    def toggle_live_mode(self):
        self.live_mode_active = not self.live_mode_active
        if self.live_mode_active:
            # Zabieramy fokus z pola tekstowego na główne okno
            self.root.focus_set()
            self.live_toggle_btn.config(
                text="TRYB LIVE: AKTYWNY – Pisz na klawiaturze! (Kliknij lub F12 by wyłączyć)",
                bg="#d4edda",
                fg="#155724",
                activebackground="#c3e6cb"
            )
            self.live_last_key_label.config(text="Oczekiwanie na klawisze...", foreground="#155724")
        else:
            self.live_toggle_btn.config(
                text="TRYB LIVE: WYŁĄCZONY (Kliknij lub wciśnij F12, aby włączyć)",
                bg="#f8d7da",
                fg="#721c24",
                activebackground="#f5c6cb"
            )
            self.live_last_key_label.config(
                text="Gdy tryb Live jest włączony, wszystko co piszesz leci prosto na telefon/PC.",
                foreground="#555555"
            )

    def on_global_keypress(self, event):
        # Klawisz F12 zawsze przełącza tryb Live
        if event.keysym == "F12":
            self.toggle_live_mode()
            return "break"

        if not self.live_mode_active:
            return

        if not self.bt_server.connected:
            self.live_last_key_label.config(text="Brak połączenia Bluetooth! Sparuj telefon/PC.", foreground="red")
            return "break"

        sent_key_name = None

        if event.keysym in KEYSYM_TO_HID:
            keycode = KEYSYM_TO_HID[event.keysym]
            modifier = 0x02 if (event.state & 0x0001) else 0x00
            sent_key_name = event.keysym
            threading.Thread(target=self.bt_server.send_hid_report, args=(modifier, keycode), daemon=True).start()
        elif event.char and event.char in CHAR_TO_HID:
            modifier, keycode = CHAR_TO_HID[event.char]
            sent_key_name = repr(event.char)
            threading.Thread(target=self.bt_server.send_hid_report, args=(modifier, keycode), daemon=True).start()

        if sent_key_name:
            self.live_last_key_label.config(text=f"Wysłano klawisz: {sent_key_name}", foreground="#155724")

        # Blokuje wpisywanie znaków do innych kontrolek, gdy tryb Live jest włączony
        return "break"

    def start_sending_text(self):
        self.disable_live_mode_if_active()

        if not self.bt_server.connected:
            messagebox.showwarning("Brak połączenia", "Najpierw połącz się z telefonem lub komputerem przez Bluetooth!")
            return

        text_to_send = self.text_box.get("1.0", tk.END)[:-1]
        if not text_to_send:
            return

        self.is_typing_text = True
        self.send_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

        delay_sec = self.delay_var.get() / 1000.0
        threading.Thread(target=self.type_text_worker, args=(text_to_send, delay_sec), daemon=True).start()

    def stop_sending_text(self):
        self.is_typing_text = False

    def type_text_worker(self, text, delay):
        for char in text:
            if not self.is_typing_text or not self.bt_server.connected:
                break
            if char in CHAR_TO_HID:
                mod, code = CHAR_TO_HID[char]
                self.bt_server.send_hid_report(mod, code)
                time.sleep(delay)

        self.is_typing_text = False
        self.root.after(0, lambda: self.send_btn.config(state="normal"))
        self.root.after(0, lambda: self.stop_btn.config(state="disabled"))


if __name__ == "__main__":
    if os.geteuid() != 0:
        print("BŁĄD: Uruchom skrypt z zachowaniem środowiska dla Wayland/X11:")
        print("      sudo -E python3 fedora_bt_keyboard.py")
        sys.exit(1)

    root = tk.Tk()
    app = BTKeyboardGUI(root)
    root.mainloop()
