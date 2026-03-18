import random

_LOWER   = list("abcdefghijklmnoprstuvxyz")
_UPPER   = list("ABCDEFGHIJKLMNOPRSTUVXYZ")
_DIGITS  = list("0123456789")
_SPECIAL = list("<>?!}{[]().,;:")
_POOL    = _LOWER + _UPPER + _DIGITS + _SPECIAL


def generate_password(length: int = 15) -> str:
    return "".join(random.choice(_POOL) for _ in range(length))
