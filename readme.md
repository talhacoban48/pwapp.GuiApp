# Password Manager

A lightweight desktop password manager built with PyQt5. All passwords are encrypted with a master password — nothing is stored in plaintext.

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

## Building an executable

```bash
pyinstaller --onefile --windowed --icon=assets/favicon.ico \
  --add-data "assets;assets" main.py
```

The resulting `.exe` will be in the `dist/` folder.

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
