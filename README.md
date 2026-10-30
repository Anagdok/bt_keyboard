# Bluetooth HID Keyboard Emulator

Program w języku Python z interfejsem graficznym (GUI), który zamienia komputer z systemem Linux w bezprzewodową klawiaturę Bluetooth (profil HID). Pozwala na połączenie laptopa z innym komputerem, telefonem (Android/iOS) lub tabletem i wysyłanie do niego znaków dokładnie tak, jakby pochodziły z fizycznej klawiatury.

## Główne funkcje

- **Tryb Live Input (Pisanie na żywo):** Po włączeniu tego trybu przyciskiem (lub klawiszem F12), program przechwytuje wciskane klawisze i natychmiast wysyła je przez Bluetooth do sparowanego urządzenia.
- **Tryb Auto-Typer (Wklej i wyślij):** Pozwala wkleić dowolny tekst do pola tekstowego, ustawić opóźnienie między znakami (w milisekundach) i automatycznie "wystukać" go na drugim urządzeniu.
- **Obsługa polskich znaków:** Wspiera polskie znaki diakrytyczne (układ Polski Programisty z użyciem prawego klawisza Alt).
- **Automatyczne parowanie:** Wbudowany agent D-Bus automatycznie akceptuje połączenia przychodzące, dzięki czemu nie trzeba ręcznie potwierdzać parowania w terminalu.

## Wymagania

Do działania programu potrzebne są:
- System operacyjny Linux (Fedora, Ubuntu, Debian lub pochodne).
- Wbudowany lub podłączony na USB adapter Bluetooth.
- Python 3 oraz pakiety systemowe do obsługi D-Bus, BlueZ i interfejsu Tkinter.
- Uprawnienia administratora (`sudo`), ponieważ standard Bluetooth HID wymaga otwarcia niskopoziomowych portów L2CAP (17 oraz 19).

---

## Przygotowanie do działania

### 1. Instalacja wymaganych pakietów

Wybierz polecenie odpowiednie dla Twojej dystrybucji:

**Fedora:**

```bash
sudo dnf install python3-dbus python3-gobject python3-tkinter bluez
```

**Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install python3-dbus python3-gi python3-tk bluez
```

### 2. Konfiguracja usługi Bluetooth (BlueZ)

Domyślnie systemowa usługa Bluetooth posiada włączoną wtyczkę `input`, która blokuje porty wymagane przez nasz emulator. Należy ją wyłączyć dla demona `bluetoothd`.

1. Otwórz edycję konfiguracji usługi systemd:

   ```bash
   sudo systemctl edit bluetooth.service
   ```

2. W otwartym edytorze wklej poniższe linie (nadpiszą one domyślny sposób uruchamiania usługi):

   ```ini
   [Service]
   ExecStart=
   ExecStart=/usr/libexec/bluetooth/bluetoothd -P input
   ```

   *(Uwaga: Na starszych wersjach Ubuntu/Debiana ścieżka do pliku wykonywalnego może wyglądać tak: `/usr/lib/bluetooth/bluetoothd -P input`. Możesz to sprawdzić poleceniem `systemctl status bluetooth`).*

3. Zapisz plik, przeładuj konfigurację i zrestartuj Bluetooth:

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart bluetooth
   ```

---

## Uruchomienie i instrukcja użycia

### 1. Uruchomienie programu

Program wymaga uprawnień roota do otwarcia gniazd Bluetooth. Aby okno graficzne otworzyło się poprawnie na nowoczesnych systemach (korzystających z serwera wyświetlania Wayland lub X11), użyj flagi `-E`, która przekazuje zmienne środowiskowe użytkownika:

```bash
sudo -E python3 bt_keyboard.py
```

### 2. Parowanie z drugim urządzeniem (PC / Android)

1. Po uruchomieniu programu Twój komputer stanie się widoczny w sieci Bluetooth pod nazwą **BT-Keyboard**.
2. Na drugim komputerze lub telefonie wejdź w ustawienia Bluetooth i wyszukaj nowe urządzenia.
3. Wybierz z listy **BT-Keyboard** i kliknij **"Paruj"**.
4. Połączenie zostanie zaakceptowane automatycznie, a status w programie zmieni się na **"Połączono aktywnie z urządzeniem"**.

### 3. Korzystanie z trybów pisania

- **Aby pisać na żywo:** Kliknij przycisk przełącznika lub wciśnij klawisz `F12`. Przycisk zmieni kolor na zielony. Od tej pory wszystko, co piszesz na klawiaturze (gdy okno programu jest aktywne), będzie wysyłane na drugie urządzenie. Aby wyłączyć ten tryb, ponownie wciśnij `F12` lub kliknij przycisk.
- **Aby wysłać gotowy tekst:** Wklej tekst w dolne pole, ustaw odstęp czasowy między znakami (domyślnie 15 ms) i kliknij **Wyślij cały tekst**. W każdej chwili możesz przerwać wysyłanie przyciskiem **Zatrzymaj**.
