import base64
import json
from pathlib import Path

from cryptography.fernet import Fernet

from utils.crypto import generate_salt, make_fernet, make_canary, check_canary

_CONFIG_FILE = "auth.json"


class AuthManager:
    """
    Manages master-password configuration.

    Stores two values in ~/pwapp/auth.json:
      - salt   : base64-encoded random bytes used for key derivation
      - canary : a Fernet-encrypted known value used to verify the password

    The master password itself is never stored anywhere.
    """

    def __init__(self, basepath: Path):
        self._config_path = basepath / _CONFIG_FILE

    # ------------------------------------------------------------------ #

    def is_configured(self) -> bool:
        """Return True if a master password has already been set up."""
        return self._config_path.exists()

    def setup(self, master_password: str) -> Fernet:
        """
        Create a new auth configuration for the given master password.
        Writes auth.json and returns a ready-to-use Fernet instance.
        Call this only on first run (when is_configured() is False).
        """
        salt = generate_salt()
        fernet = make_fernet(master_password, salt)
        canary = make_canary(fernet)

        config = {
            "salt":   base64.b64encode(salt).decode(),
            "canary": canary,
        }
        self._config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
        return fernet

    def login(self, master_password: str) -> Fernet | None:
        """
        Verify master_password against the stored canary.
        Returns a Fernet instance on success, None on wrong password.
        """
        config = json.loads(self._config_path.read_text(encoding="utf-8"))
        salt   = base64.b64decode(config["salt"])
        canary = config["canary"]

        fernet = make_fernet(master_password, salt)
        return fernet if check_canary(canary, fernet) else None
