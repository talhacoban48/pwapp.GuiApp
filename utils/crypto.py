import base64
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Known plaintext used to verify a master password is correct.
# If decrypting this canary succeeds, the password (and derived key) is valid.
_CANARY = b"pwapp-canary-v1"

# PBKDF2 iteration count — high enough to be slow for brute-force,
# fast enough not to annoy the user on login.
_ITERATIONS = 480_000


def generate_salt() -> bytes:
    """Return 32 cryptographically random bytes."""
    return os.urandom(32)


def derive_key(master_password: str, salt: bytes) -> bytes:
    """
    Derive a 256-bit Fernet-compatible key from master_password + salt
    using PBKDF2-HMAC-SHA256.
    Returns the key as a URL-safe base64-encoded bytes object.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(master_password.encode("utf-8")))


def make_fernet(master_password: str, salt: bytes) -> Fernet:
    """Derive key and return a ready-to-use Fernet instance."""
    return Fernet(derive_key(master_password, salt))


def make_canary(fernet: Fernet) -> str:
    """Encrypt the canary value; store the result to verify future logins."""
    return fernet.encrypt(_CANARY).decode()


def check_canary(canary_token: str, fernet: Fernet) -> bool:
    """Return True if fernet can decrypt canary_token to the expected value."""
    try:
        return fernet.decrypt(canary_token.encode()) == _CANARY
    except (InvalidToken, Exception):
        return False


def encrypt(plaintext: str, fernet: Fernet) -> str:
    """Encrypt a string; returns the Fernet token as a string."""
    if not plaintext:
        return plaintext
    return fernet.encrypt(plaintext.encode("utf-8")).decode()


def decrypt(token: str, fernet: Fernet) -> str:
    """Decrypt a Fernet token string; returns the original plaintext."""
    if not token:
        return token
    return fernet.decrypt(token.encode()).decode("utf-8")


def looks_encrypted(value: str) -> bool:
    """
    Heuristic: Fernet tokens always start with 'gAAAAA' (the base64 encoding
    of the Fernet magic byte 0x80 plus version/timestamp header).
    Used during migration to avoid double-encrypting.
    """
    return isinstance(value, str) and value.startswith("gAAAAA")
