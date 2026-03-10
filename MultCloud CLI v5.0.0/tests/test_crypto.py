"""Tests for the MultCloud crypto module."""

import json

from multcloud.crypto import (
    DECRYPT_KEY,
    ENCRYPT_KEY,
    aes_decrypt,
    aes_encrypt,
    sign_md5,
    sign_with_aes_key,
    sign_with_salt,
)


class TestAESEncryptDecrypt:
    """Test AES-ECB encrypt/decrypt round-trip."""

    def test_encrypt_decrypt_roundtrip(self):
        """Encrypt then decrypt should return original data."""
        original = {"status": 200, "message": "OK"}
        plaintext = json.dumps(original)

        # Encrypt with encrypt key, decrypt with same key
        ciphertext = aes_encrypt(plaintext, ENCRYPT_KEY)
        result = aes_decrypt(ciphertext, ENCRYPT_KEY)
        assert result == original

    def test_encrypt_produces_hex(self):
        """Encrypted output should be uppercase hex string."""
        ciphertext = aes_encrypt("hello world")
        assert all(c in "0123456789ABCDEF" for c in ciphertext)

    def test_decrypt_strips_quotes(self):
        """Decrypt should handle quoted hex strings."""
        plaintext = json.dumps({"test": True})
        ciphertext = aes_encrypt(plaintext, ENCRYPT_KEY)
        quoted = f'"{ciphertext}"'
        result = aes_decrypt(quoted, ENCRYPT_KEY)
        assert result == {"test": True}

    def test_encrypt_different_keys_produce_different_output(self):
        """Different keys should produce different ciphertext."""
        plaintext = "test data"
        ct1 = aes_encrypt(plaintext, ENCRYPT_KEY)
        ct2 = aes_encrypt(plaintext, DECRYPT_KEY)
        assert ct1 != ct2


class TestSignMD5:
    """Test the MD5 signing algorithm."""

    def test_empty_params(self):
        """Empty params dict should return a hash."""
        result = sign_md5({})
        # MD5 of "" is d41d8cd98f00b204e9800998ecf8427e
        # Strip [1:-2] = 41d8cd98f00b204e9800998ecf8427
        assert isinstance(result, str)
        assert len(result) == 29  # 32 - 3 (strip first and last 2)

    def test_single_param(self):
        """Single param should produce consistent hash."""
        result1 = sign_md5({"key": "value"})
        result2 = sign_md5({"key": "value"})
        assert result1 == result2

    def test_order_independence(self):
        """
        Keys are sorted, so different insertion order should produce same hash.
        """
        result1 = sign_md5({"a": "1", "b": "2", "c": "3"})
        result2 = sign_md5({"c": "3", "a": "1", "b": "2"})
        assert result1 == result2

    def test_boolean_values(self):
        """Boolean values should be lowercased strings."""
        result = sign_md5({"flag": True})
        assert isinstance(result, str)
        assert len(result) == 29

    def test_dict_value_hashed(self):
        """Dict values should be JSON-serialized, sorted, then MD5'd."""
        result = sign_md5({"data": {"nested": "value"}})
        assert isinstance(result, str)
        assert len(result) == 29

    def test_list_value_hashed(self):
        """List values should be JSON-serialized, sorted, then MD5'd."""
        result = sign_md5({"items": [1, 2, 3]})
        assert isinstance(result, str)
        assert len(result) == 29

    def test_ascending_keys_descending_values(self):
        """
        Verify the key-value pairing: keys ascending, values descending.
        With keys [a, b, c] and values [va, vb, vc]:
        concat = "a" + inspect(vc) + "b" + inspect(vb) + "c" + inspect(va)
        """
        # We can't easily verify the internal concat without exposing it,
        # but we can verify that changing a value changes the signature
        result1 = sign_md5({"a": "1", "b": "2", "c": "3"})
        result2 = sign_md5({"a": "1", "b": "2", "c": "CHANGED"})
        assert result1 != result2


class TestSignWithSalt:
    """Test salt-based signing."""

    def test_adds_s_param(self):
        """Should add 's' parameter to result."""
        result = sign_with_salt({"ud": "123"}, "mysalt")
        assert "s" in result
        assert "salt" not in result  # salt should be removed

    def test_preserves_original_params(self):
        """Should keep original parameters."""
        result = sign_with_salt({"ud": "123", "type": 1}, "mysalt")
        assert result["ud"] == "123"
        assert result["type"] == 1
        assert "s" in result

    def test_does_not_mutate_input(self):
        """Should not modify the input dict."""
        original = {"ud": "123"}
        sign_with_salt(original, "mysalt")
        assert "s" not in original
        assert "salt" not in original


class TestSignWithAESKey:
    """Test AES-key-based signing."""

    def test_adds_s_param(self):
        """Should add 's' parameter to result."""
        result = sign_with_aes_key({"email": "test@test.com"})
        assert "s" in result
        assert "aesKey" not in result  # aesKey should be removed

    def test_preserves_original_params(self):
        """Should keep original parameters."""
        result = sign_with_aes_key({"email": "test@test.com", "password": "pwd"})
        assert result["email"] == "test@test.com"
        assert result["password"] == "pwd"
        assert "s" in result

    def test_does_not_mutate_input(self):
        """Should not modify the input dict."""
        original = {"email": "test@test.com"}
        sign_with_aes_key(original)
        assert "s" not in original
        assert "aesKey" not in original
