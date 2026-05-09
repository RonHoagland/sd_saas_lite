"""Custom Django model fields.

EncryptedCharField / EncryptedTextField transparently encrypt and decrypt
string values via config.encryption. Storage on disk is TEXT (varchar with no
length cap) since ciphertext is always larger than plaintext; ``max_length``
on the field validates the *plaintext* length only.
"""

from __future__ import annotations

from django.db import models

from .encryption import decrypt, encrypt


class _EncryptedStringMixin:
    """Shared encryption behaviour for char- and text-backed fields."""

    def get_internal_type(self) -> str:
        return "TextField"

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return decrypt(value)

    def to_python(self, value):
        if value is None:
            return value
        if isinstance(value, str) and value.startswith("v1:"):
            return decrypt(value)
        return value

    def get_prep_value(self, value):
        if value is None:
            return value
        return encrypt(str(value))


class EncryptedCharField(_EncryptedStringMixin, models.CharField):
    """CharField whose value is encrypted at rest via config.encryption.

    Set ``max_length`` to constrain the plaintext input. The DB column is
    TEXT, so ciphertext expansion does not require manual sizing.
    """


class EncryptedTextField(_EncryptedStringMixin, models.TextField):
    """TextField whose value is encrypted at rest via config.encryption."""
