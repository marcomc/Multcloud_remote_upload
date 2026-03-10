"""
Cryptographic utilities for MultCloud API communication.

MultCloud uses:
- AES-ECB with PKCS7 padding for response decryption
- MD5-based request signing with a specific key/value ordering scheme
- Two signing modes: salt-based (authenticated) and AES-key-based (unauthenticated)
"""

import hashlib
import json
from base64 import b64decode, b64encode

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# Current keys extracted from MultCloud's frontend JS (March 2026)
# These may change when MultCloud updates their frontend
ENCRYPT_KEY = "KXrDPHUkQSMKhklkKHHP+Q=="
DECRYPT_KEY = "LIa4CTfB3SwKnfJhu2iJkQ=="


def aes_decrypt(ciphertext_hex: str, key: str = DECRYPT_KEY) -> dict:
    """Decrypt an AES-ECB encrypted hex string from MultCloud API responses.

    Args:
        ciphertext_hex: Hex-encoded AES ciphertext.
        key: Base64-encoded AES key (default: DECRYPT_KEY).

    Returns:
        Decoded JSON object.
    """
    ciphertext_hex = ciphertext_hex.strip('"')
    key_bytes = b64decode(key)
    cipher = AES.new(key_bytes, AES.MODE_ECB)
    ciphertext = bytes.fromhex(ciphertext_hex)
    plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
    return json.loads(plaintext.decode("utf-8"))


def aes_encrypt(plaintext: str, key: str = ENCRYPT_KEY) -> str:
    """Encrypt a string using AES-ECB for MultCloud API requests.

    Args:
        plaintext: String to encrypt.
        key: Base64-encoded AES key (default: ENCRYPT_KEY).

    Returns:
        Hex-encoded ciphertext.
    """
    key_bytes = b64decode(key)
    cipher = AES.new(key_bytes, AES.MODE_ECB)
    padded = pad(plaintext.encode("utf-8"), AES.block_size)
    return cipher.encrypt(padded).hex().upper()


def _inspect_value(value) -> str:
    """Convert a value to its signing representation.

    Objects/arrays are JSON-serialized, sorted char-by-char, then MD5-hashed.
    Booleans are lowercased strings.
    Everything else is converted to string directly.
    """
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (dict, list)):
        serialized = json.dumps(value, separators=(",", ":"))
        sorted_chars = "".join(sorted(serialized))
        return hashlib.md5(sorted_chars.encode("utf-8")).hexdigest()
    return str(value)


def sign_md5(params: dict) -> str:
    """Calculate the MD5 signature for a set of request parameters.

    Algorithm:
    1. Sort all parameter keys alphabetically.
    2. Pair keys in ascending order with values in DESCENDING key order.
    3. Concatenate: key[0] + inspect(value[last]) + key[1] + inspect(value[second-to-last]) + ...
    4. MD5 hash the concatenated string.
    5. Return hash[1:-2] (strip first char and last two chars).
    """
    keys = sorted(params.keys())
    n = len(keys)
    concat = ""
    for i in range(n):
        val = params[keys[n - i - 1]]
        concat += keys[i] + _inspect_value(val)
    md5_hash = hashlib.md5(concat.encode("utf-8")).hexdigest()
    return md5_hash[1:-2]


def sign_with_salt(params: dict, salt: str) -> dict:
    """Sign parameters using the user's salt (for authenticated requests).

    Args:
        params: Request parameters dict. May already contain 'salt'.
        salt: User salt from login response.

    Returns:
        Signed parameters dict with 's' field added, 'salt' removed.
    """
    params = dict(params)
    params["salt"] = salt
    params["s"] = sign_md5(params)
    params.pop("salt", None)
    return params


def sign_with_aes_key(params: dict, aes_key: str = ENCRYPT_KEY) -> dict:
    """Sign parameters using the AES encrypt key (for unauthenticated requests).

    Args:
        params: Request parameters dict.
        aes_key: AES key to use for signing (default: ENCRYPT_KEY).

    Returns:
        Signed parameters dict with 's' field added, 'aesKey' removed.
    """
    params = dict(params)
    params["aesKey"] = aes_key
    params["s"] = sign_md5(params)
    params.pop("aesKey", None)
    return params
