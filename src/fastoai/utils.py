import json
import secrets
from datetime import UTC, datetime
from functools import partial

from pydantic import BaseModel

RANDOM_STRING_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def get_random_string(length, allowed_chars=RANDOM_STRING_CHARS):
    """Return a securely generated random string.

    The bit length of the returned value can be calculated with the formula:
        log_2(len(allowed_chars)^length)

    For example, with default `allowed_chars` (26+26+10), this gives:
      * length: 12, bit length =~ 71 bits
      * length: 22, bit length =~ 131 bits
    """
    return "".join(secrets.choice(allowed_chars) for _ in range(length))


random_id = partial(get_random_string, 24)  # (26 * 2 + 10) ^ 24 > uuid4


def random_id_with_prefix(prefix: str):
    def _inner():
        return f"{prefix}{random_id()}"

    return _inner


def now():
    return datetime.now(UTC)


def json_serializer(model: BaseModel):
    return model.model_dump_json()


def json_deserializer(data: str):
    assert isinstance(json.loads(data), dict) and "object" in json, "Invalid JSON data"
