"""test_license_tiers — License system unit tests with mocking.

Tests LicenseManager: tier detection, universe validation, AES encryption,
RSA verification, trial period, revocation URL SSRF protection.

Topic: testing
Last Updated: 2026-05-02 14:36
"""

import pytest
import json
import os
import tempfile
import base64
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, PropertyMock
from pathlib import Path

# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _isolate_config(tmp_path, monkeypatch):
    """Isolate license manager from real filesystem and hardware."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Patch module-level paths BEFORE importing
    monkeypatch.setattr("src.utils.license.CONFIG_DIR", config_dir)
    monkeypatch.setattr("src.utils.license.LICENSE_FILE", config_dir / "license.lic")
    monkeypatch.setattr("src.utils.license.REVOCATION_CACHE_FILE", config_dir / "revocation_cache.json")
    monkeypatch.setattr("src.utils.license.INSTALL_DATE_FILE", config_dir / "install_date.txt")
    monkeypatch.setattr("src.utils.license.get_config_dir", lambda: config_dir)

    # Patch hardware ID to deterministic value
    monkeypatch.setattr("src.utils.license.LicenseManager._get_hardware_id",
                        lambda self: "a" * 64)


@pytest.fixture
def lm():
    """Create a fresh LicenseManager instance."""
    from src.utils.license import LicenseManager
    return LicenseManager()


@pytest.fixture
def lm_with_license(lm, tmp_path):
    """LicenseManager with a fake valid license file."""
    license_file = tmp_path / "config" / "license.lic"

    # Build fake license data
    license_data = {
        "device_id": lm._device_id,
        "license_id": "test-uuid-1234",
        "issued_date": "2026-05-01T00:00:00",
        "customer_email": "test@example.com",
        "signature": base64.b64encode(b"fake_signature").decode(),
    }

    # Encrypt with the manager's AES key
    encrypted = lm._encrypt_license_data(license_data)
    license_file.write_bytes(encrypted)

    return lm


# ── 1. Device ID ──────────────────────────────────────────────────────────

class TestDeviceID:
    def test_device_id_is_64_hex(self, lm):
        assert len(lm._device_id) == 64
        assert all(c in "0123456789abcdef" for c in lm._device_id)

    def test_get_device_id_returns_same(self, lm):
        assert lm.get_device_id() == lm._device_id


# ── 2. Trial Period ───────────────────────────────────────────────────────

class TestTrialPeriod:
    def test_trial_info_first_run(self, lm):
        info = lm.get_trial_info()
        assert info["is_trial"] is True
        assert info["days_remaining"] == 7
        assert info["is_expired"] is False

    def test_trial_expired(self, lm, tmp_path):
        install_file = tmp_path / "config" / "install_date.txt"
        expired = datetime.now() - timedelta(days=10)
        install_file.write_text(expired.isoformat())

        info = lm.get_trial_info()
        assert info["is_expired"] is True
        assert info["days_remaining"] == 0

    def test_trial_partial(self, lm, tmp_path):
        install_file = tmp_path / "config" / "install_date.txt"
        partial = datetime.now() - timedelta(days=3)
        install_file.write_text(partial.isoformat())

        info = lm.get_trial_info()
        assert info["days_remaining"] == 4


# ── 3. License Tiers ──────────────────────────────────────────────────────

class TestLicenseTiers:
    def test_free_tier_no_license(self, lm):
        assert lm.get_license_tier() == "FREE"

    def test_free_max_universes(self, lm):
        assert lm.get_max_universes() == 4

    def test_free_is_not_admin(self, lm):
        assert lm.is_admin() is False

    def test_free_is_valid_with_trial(self, lm):
        valid, msg = lm.is_valid()
        assert valid is True
        assert "Trial" in msg

    def test_expired_trial_not_valid(self, lm, tmp_path):
        install_file = tmp_path / "config" / "install_date.txt"
        expired = datetime.now() - timedelta(days=10)
        install_file.write_text(expired.isoformat())

        valid, msg = lm.is_valid()
        assert valid is False
        assert "expired" in msg.lower()


# ── 4. Universe Validation ────────────────────────────────────────────────

class TestUniverseValidation:
    @pytest.mark.parametrize("universe", [0, 1, 2, 3])
    def test_free_valid_univers(self, lm, universe):
        ok, msg = lm.validate_universe(universe)
        assert ok is True

    @pytest.mark.parametrize("universe", [4, 5, 100, 511])
    def test_free_invalid_univers(self, lm, universe):
        ok, msg = lm.validate_universe(universe)
        assert ok is False
        assert "FREE" in msg

    def test_negative_universe(self, lm):
        ok, msg = lm.validate_universe(-1)
        assert ok is False

    def test_universe_999(self, lm):
        ok, msg = lm.validate_universe(999)
        assert ok is False


# ── 5. AES Encryption / Decryption ───────────────────────────────────────

class TestAESEncryption:
    def test_encrypt_decrypt_roundtrip(self, lm):
        data = {"key": "value", "number": 42}
        encrypted = lm._encrypt_license_data(data)
        assert isinstance(encrypted, bytes)
        assert len(encrypted) > 12  # nonce + ciphertext

        decrypted = lm._decrypt_license_data(encrypted)
        assert decrypted == data

    def test_decrypt_tampered_fails(self, lm):
        data = {"test": True}
        encrypted = bytearray(lm._encrypt_license_data(data))
        encrypted[-1] ^= 0xFF  # Flip last byte
        with pytest.raises(ValueError, match="corrupted"):
            lm._decrypt_license_data(bytes(encrypted))

    def test_decrypt_wrong_key_fails(self, lm, monkeypatch):
        data = {"test": True}
        encrypted = lm._encrypt_license_data(data)

        # Change AES key by changing device ID
        monkeypatch.setattr(lm, "_device_id", "b" * 64)
        lm._aes_key = lm._derive_aes_key()

        with pytest.raises(ValueError):
            lm._decrypt_license_data(encrypted)


# ── 6. RSA Offline Validation ─────────────────────────────────────────────

class TestRSAValidation:
    def test_invalid_signature_rejected(self, lm):
        license_data = {
            "device_id": lm._device_id,
            "license_id": "test-uuid",
            "issued_date": "2026-05-01",
            "signature": base64.b64encode(b"garbage_signature").decode(),
        }
        assert lm._validate_license_offline(license_data) is False

    def test_wrong_device_id_rejected(self, lm):
        license_data = {
            "device_id": "wrong_device_id",
            "license_id": "test-uuid",
            "issued_date": "2026-05-01",
            "signature": base64.b64encode(b"sig").decode(),
        }
        assert lm._validate_license_offline(license_data) is False

    def test_missing_fields_rejected(self, lm):
        assert lm._validate_license_offline({}) is False

    def test_no_public_key_rejected(self, lm):
        lm._public_key = None
        license_data = {
            "device_id": lm._device_id,
            "signature": base64.b64encode(b"sig").decode(),
        }
        assert lm._validate_license_offline(license_data) is False


# ── 7. License File Operations ────────────────────────────────────────────

class TestLicenseFile:
    def test_save_and_load(self, lm, tmp_path):
        license_file = tmp_path / "config" / "license.lic"
        data = {
            "device_id": lm._device_id,
            "license_id": "uuid-123",
            "issued_date": "2026-05-01",
        }
        lm._save_license(data)
        assert license_file.exists()

        loaded = lm._load_license()
        assert loaded is not None
        assert loaded["license_id"] == "uuid-123"

    def test_load_no_file_returns_none(self, lm):
        assert lm._load_license() is None

    def test_load_corrupted_returns_none(self, lm, tmp_path):
        license_file = tmp_path / "config" / "license.lic"
        license_file.write_bytes(b"not_valid_encrypted_data")
        assert lm._load_license() is None


# ── 8. SSRF Protection ────────────────────────────────────────────────────

class TestSSRFProtection:
    def test_valid_url_allowed(self, lm):
        assert lm._validate_revocation_url("http://localhost:5000/api") is True

    def test_https_allowed(self, lm):
        assert lm._validate_revocation_url("https://license.truongcongdinh.org/api") is True

    def test_ftp_scheme_blocked(self, lm):
        assert lm._validate_revocation_url("ftp://evil.com") is False

    def test_file_scheme_blocked(self, lm):
        assert lm._validate_revocation_url("file:///etc/passwd") is False

    def test_no_scheme_blocked(self, lm):
        assert lm._validate_revocation_url("not_a_url") is False


# ── 9. License Activation ─────────────────────────────────────────────────

class TestActivation:
    def test_invalid_json_rejected(self, lm):
        ok, msg = lm.activate_license("not json")
        assert ok is False
        assert "format" in msg.lower()

    def test_invalid_signature_rejected(self, lm):
        license_json = json.dumps({
            "device_id": lm._device_id,
            "license_id": "uuid",
            "issued_date": "2026-05-01",
            "signature": base64.b64encode(b"fake").decode(),
        })
        ok, msg = lm.activate_license(license_json)
        assert ok is False


# ── 10. Global Instance ───────────────────────────────────────────────────

class TestGlobalInstance:
    def test_get_license_manager_returns_instance(self):
        from src.utils.license import get_license_manager, _license_manager
        # Reset global to force new creation with patched paths
        import src.utils.license as mod
        mod._license_manager = None
        lm = get_license_manager()
        assert lm is not None
        mod._license_manager = None  # cleanup


# ── 11. License Info ──────────────────────────────────────────────────────

class TestLicenseInfo:
    def test_info_free_tier(self, lm):
        info = lm.get_license_info()
        assert info["device_id"] == lm._device_id
        assert info["is_licensed"] is True  # trial counts
        assert info["license_data"] is None

    def test_info_contains_trial_days(self, lm):
        info = lm.get_license_info()
        assert info["trial_days_remaining"] == 7