# Password Manager

A lightweight desktop password manager built with PyQt5. All passwords are encrypted with a master password — nothing is stored in plaintext.



## Download

**[PasswordManagerSetup_1.0.0.exe](https://github.com/talhacoban48/pwapp.GuiApp/releases/download/v1.0.0/PasswordManagerSetup_1.0.0.exe)**


---

## Features

- **Master password authentication** — PBKDF2-HMAC-SHA256 key derivation, canary-based verification (master password is never stored)
- **Fernet encryption** — every password in the database is encrypted at rest
- **Dark UI** — clean dark theme with colored panel headers and role-colored action buttons
- **Live search** — 500 ms debounced, case-insensitive search on app name with a clear button
- **Import / Export** — CSV and Excel (`.xlsx`) support with merge logic (last-write-wins on `updatedDate`)
- **Password generator** — one-click random password generation
- **Active / Passive entries** — toggle visibility of deactivated records from the Settings menu
- **Change master password** — re-encrypts the entire database with the new key
- **PyInstaller ready** — resource paths resolve correctly inside a frozen `.exe`

---

## Requirements

- Python 3.10+
- Dependencies listed in `requirements.txt`

```
PyQt5>=5.15
openpyxl>=3.0
cryptography>=42.0
pyinstaller>=6.0
```

Install:

```bash
pip install -r requirements.txt
```

---

## Running

```bash
python main.py
```

On first launch you will be prompted to create a master password (minimum 4 characters). This password is required every time you open the app. **If you forget it, your data cannot be recovered.**

---

## Data storage

All data is stored under `~/pwapp/` (your home directory):

| File | Contents |
|---|---|
| `pwapp.db` | SQLite database with encrypted passwords |
| `auth.json` | Salt and canary used to verify the master password |

---

## Building an installer

### Prerequisites

| Tool | Purpose | Download |
|---|---|---|
| Python 3.10+ | Run the app / build tools | [python.org](https://www.python.org/downloads/) |
| PyInstaller | Package app into a single `.exe` | `pip install pyinstaller` |
| Inno Setup 6 | Create the Windows installer | [jrsoftware.org/isinfo.php](https://jrsoftware.org/isinfo.php) |

### Steps

**1. Install Python dependencies**

```bash
pip install -r requirements.txt
```

**2. Build the executable**

```bash
pyinstaller pwapp.spec --clean --noconfirm
```

Output: `dist\PasswordManager.exe`

**3. Build the installer**

```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

Output: `installer_output\PasswordManagerSetup_1.0.0.exe`

### One-step build (Windows)

Runs both steps automatically:

```bash
build.bat
```

> Inno Setup must be installed before running `build.bat`.

---

## Project structure

```
pwapp/
├── main.py
├── requirements.txt
├── assets/
│   └── *.ico
├── database/
│   └── db_manager.py      # SQLite + Fernet encrypt/decrypt
├── ui/
│   ├── main_window.py
│   ├── login_dialog.py
│   ├── change_password_dialog.py
│   └── widgets.py
└── utils/
    ├── auth_manager.py    # Master password setup & login
    ├── crypto.py          # Key derivation, Fernet helpers
    ├── local_manager.py   # Locale setup
    ├── password_gen.py    # Random password generator
    └── resources.py       # PyInstaller path helper
```

---

## License

MIT
