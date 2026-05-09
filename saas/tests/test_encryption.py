"""Tests for config/encryption.py and config/fields.py."""

from django.test import TestCase

from config.encryption import decrypt, encrypt


class EncryptionRoundtripTest(TestCase):

    def test_roundtrip_simple(self):
        self.assertEqual(decrypt(encrypt('hello')), 'hello')

    def test_roundtrip_unicode(self):
        self.assertEqual(decrypt(encrypt('héllo — 世界')), 'héllo — 世界')

    def test_empty_in_empty_out(self):
        self.assertEqual(encrypt(''), '')
        self.assertEqual(decrypt(''), '')

    def test_none_in_empty_out(self):
        self.assertEqual(encrypt(None), '')
        self.assertEqual(decrypt(None), '')

    def test_ciphertext_uses_v1_prefix(self):
        ct = encrypt('foo')
        self.assertTrue(ct.startswith('v1:'))

    def test_each_call_uses_fresh_nonce(self):
        # SecretBox.encrypt() generates a random nonce per call; identical
        # plaintext must NOT produce identical ciphertext.
        a = encrypt('same plaintext')
        b = encrypt('same plaintext')
        self.assertNotEqual(a, b)
        self.assertEqual(decrypt(a), decrypt(b))

    def test_unknown_prefix_raises(self):
        with self.assertRaises(ValueError):
            decrypt('v9:somethingbogus')

    def test_tampered_ciphertext_raises(self):
        ct = encrypt('hello')
        tampered = ct[:-4] + 'AAAA'
        with self.assertRaises(ValueError):
            decrypt(tampered)
