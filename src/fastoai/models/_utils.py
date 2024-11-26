import secrets
from datetime import UTC, datetime
from string import ascii_letters, digits


def get_random_string(length, allowed_chars=ascii_letters + digits):
    """Return a securely generated random string.

    The bit length of the returned value can be calculated with the formula:
        log_2(len(allowed_chars)^length)

    For example, with default `allowed_chars` (26+26+10), this gives:
      * length: 12, bit length =~ 71 bits
      * length: 22, bit length =~ 131 bits
    """
    return "".join(secrets.choice(allowed_chars) for _ in range(length))


def random_id_with_prefix(prefix: str):
    def _inner():
        return f"{prefix}{get_random_string(24)}"  # (26 * 2 + 10) ^ 24 > uuid4

    return _inner


def now():
    return datetime.now(UTC)
