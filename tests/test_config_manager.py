"""test_config_manager — Unit tests cho Configuration Manager.

Tests: Validation, Migration, CRUD, backup/restore, license encryption.

Wing: code_chronicles
Topic: unit_testing
Last Updated: 2026-05-01 23:37
"""

import json
import base64
import unittest
from pathlib import Path
from unittest.mock import patch
import tempfile
import shutil

from src.system.config_manager import (
    ConfigManager,
    ConfigValidator,
    ConfigMigration,
    DEFAULT_CONFIG,
    CONFIG_VERSION,
)


class TestConfigValidatorNetwork(unittest.TestCase):
    """Network config validation"""

    def test_valid_network_defaults(self):
        errors = ConfigValidator.validate_network(DEFAULT_CONFIG)
        self.assertEqual(errors, [])

    def test_port_too_low(self):
        cfg = {"network": {"artnet_port": 80}}
        errors = ConfigValidator.validate_network(cfg)
        self.assertEqual(len(errors), 1)
        self.assertIn("artnet_port", errors[0])

    def test_port_too_high(self):
        cfg = {"network": {"artnet_port": 70000}}
        errors = ConfigValidator.validate_network(cfg)
        self.assertEqual(len(errors), 1)

    def test_port_boundary_low(self):
        cfg = {"network": {"artnet_port": 1024}}
        errors = ConfigValidator.validate_network(cfg)
        self.assertEqual(errors, [])

    def test_port_boundary_high(self):
        cfg = {"network": {"artnet_port": 65535}}
        errors = ConfigValidator.validate_network(cfg)
        self.assertEqual(errors, [])

    def test_timeout_too_low(self):
        cfg = {"network": {"timeout": 0.01}}
        errors = ConfigValidator.validate_network(cfg)
        self.assertEqual(len(errors), 1)
        self.assertIn("timeout", errors[0])

    def test_timeout_too_high(self):
        cfg = {"network": {"timeout": 100.0}}
        errors = ConfigValidator.validate_network(cfg)
        self.assertEqual(len(errors), 1)

    def test_missing_network_key(self):
        """Gracefully handles missing network section"""
        errors = ConfigValidator.validate_network({})
        self.assertEqual(errors, [])


class TestConfigValidatorRecording(unittest.TestCase):
    """Recording config validation"""

    def test_valid_recording_defaults(self):
        errors = ConfigValidator.validate_recording(DEFAULT_CONFIG)
        self.assertEqual(errors, [])

    def test_fps_too_low(self):
        cfg = {"recording": {"fps": 0}}
        errors = ConfigValidator.validate_recording(cfg)
        self.assertTrue(any("FPS" in e for e in errors))

    def test_fps_too_high(self):
        cfg = {"recording": {"fps": 200}}
        errors = ConfigValidator.validate_recording(cfg)
        self.assertTrue(any("FPS" in e for e in errors))

    def test_fps_boundary(self):
        cfg = {"recording": {"fps": 1}}
        self.assertEqual(ConfigValidator.validate_recording(cfg), [])
        cfg = {"recording": {"fps": 120}}
        self.assertEqual(ConfigValidator.validate_recording(cfg), [])

    def test_invalid_format(self):
        cfg = {"recording": {"format": "xml"}}
        errors = ConfigValidator.validate_recording(cfg)
        self.assertTrue(any("format" in e for e in errors))

    def test_valid_formats(self):
        for fmt in ["binary", "json"]:
            cfg = {"recording": {"format": fmt}}
            errors = ConfigValidator.validate_recording(cfg)
            self.assertEqual(errors, [], f"Format '{fmt}' should be valid")

    def test_buffer_size_out_of_range(self):
        cfg = {"recording": {"buffer_size": 5}}
        errors = ConfigValidator.validate_recording(cfg)
        self.assertTrue(any("buffer_size" in e for e in errors))

    def test_buffer_size_boundary(self):
        cfg = {"recording": {"buffer_size": 10}}
        self.assertEqual(ConfigValidator.validate_recording(cfg), [])
        cfg = {"recording": {"buffer_size": 1000}}
        self.assertEqual(ConfigValidator.validate_recording(cfg), [])


class TestConfigValidatorUI(unittest.TestCase):
    """UI config validation"""

    def test_valid_ui_defaults(self):
        errors = ConfigValidator.validate_ui(DEFAULT_CONFIG)
        self.assertEqual(errors, [])

    def test_invalid_theme(self):
        cfg = {"ui": {"theme": "neon"}}
        errors = ConfigValidator.validate_ui(cfg)
        self.assertTrue(any("theme" in e for e in errors))

    def test_valid_themes(self):
        for theme in ["dark", "light", "auto"]:
            cfg = {"ui": {"theme": theme}}
            self.assertEqual(ConfigValidator.validate_ui(cfg), [])

    def test_invalid_language(self):
        cfg = {"ui": {"language": "fr"}}
        errors = ConfigValidator.validate_ui(cfg)
        self.assertTrue(any("language" in e for e in errors))

    def test_window_too_small(self):
        cfg = {"ui": {"window_width": 320, "window_height": 200}}
        errors = ConfigValidator.validate_ui(cfg)
        self.assertTrue(any("too small" in e for e in errors))

    def test_window_min_valid(self):
        cfg = {"ui": {"window_width": 640, "window_height": 480}}
        errors = ConfigValidator.validate_ui(cfg)
        self.assertEqual(errors, [])


class TestConfigValidatorAll(unittest.TestCase):
    """Full config validation"""

    def test_default_config_is_valid(self):
        errors = ConfigValidator.validate_all(DEFAULT_CONFIG)
        self.assertEqual(errors, [])

    def test_multiple_errors(self):
        cfg = {
            "network": {"artnet_port": 80, "timeout": 0.01},
            "recording": {"fps": 0, "format": "xml"},
            "ui": {"theme": "neon", "language": "fr", "window_width": 100, "window_height": 100}
        }
        errors = ConfigValidator.validate_all(cfg)
        self.assertGreater(len(errors), 3)


class TestConfigMigration(unittest.TestCase):
    """Config version migration"""

    def test_migrate_1_0_to_2_0_adds_playback(self):
        cfg = {"version": "1.0.0", "recording": {"fps": 30}}
        result = ConfigMigration.migrate_1_0_to_2_0(cfg)
        self.assertIn("playback", result)
        self.assertEqual(result["version"], "2.0.0")

    def test_migrate_1_0_to_2_0_adds_crash_reporting(self):
        cfg = {"version": "1.0.0", "recording": {}}
        result = ConfigMigration.migrate_1_0_to_2_0(cfg)
        self.assertIn("crash_reporting", result)

    def test_migrate_1_0_to_2_0_adds_buffer_and_compression(self):
        cfg = {"version": "1.0.0", "recording": {"fps": 30}}
        result = ConfigMigration.migrate_1_0_to_2_0(cfg)
        self.assertEqual(result["recording"]["buffer_size"], 100)
        self.assertTrue(result["recording"]["compression"])

    def test_migrate_1_0_to_2_0_sets_timestamp(self):
        cfg = {"version": "1.0.0", "recording": {}}
        result = ConfigMigration.migrate_1_0_to_2_0(cfg)
        self.assertIsNotNone(result["last_updated"])

    def test_migrate_dispatches_correctly(self):
        cfg = {"version": "1.0.0", "recording": {}}
        result = ConfigMigration.migrate(cfg, "1.0.0", "2.0.0")
        self.assertEqual(result["version"], "2.0.0")

    def test_migrate_no_path_returns_unchanged(self):
        cfg = {"version": "0.5.0"}
        result = ConfigMigration.migrate(cfg, "0.5.0", "2.0.0")
        self.assertEqual(result["version"], "0.5.0")


class TestConfigManagerCRUD(unittest.TestCase):
    """ConfigManager get/set with temp files"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_path = Path(self.tmpdir) / "test_config.json"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _make_manager(self):
        """Create ConfigManager with temp file"""
        return ConfigManager(config_file=self.config_path)

    def test_init_creates_default_config(self):
        mgr = self._make_manager()
        self.assertEqual(mgr.config["version"], CONFIG_VERSION)
        self.assertTrue(self.config_path.exists())

    def test_get_dot_notation(self):
        mgr = self._make_manager()
        self.assertEqual(mgr.get("network.artnet_port"), 6454)
        self.assertEqual(mgr.get("ui.theme"), "dark")
        self.assertEqual(mgr.get("recording.fps"), 60)

    def test_get_top_level(self):
        mgr = self._make_manager()
        self.assertEqual(mgr.get("version"), CONFIG_VERSION)

    def test_get_missing_returns_default(self):
        mgr = self._make_manager()
        self.assertIsNone(mgr.get("nonexistent.key"))
        self.assertEqual(mgr.get("nonexistent", "fallback"), "fallback")

    def test_set_dot_notation(self):
        mgr = self._make_manager()
        mgr.set("network.artnet_port", 7000, auto_save=False)
        self.assertEqual(mgr.get("network.artnet_port"), 7000)

    def test_set_creates_nested(self):
        mgr = self._make_manager()
        mgr.set("custom.section.value", 42, auto_save=False)
        self.assertEqual(mgr.get("custom.section.value"), 42)

    def test_set_auto_save_persists(self):
        mgr = self._make_manager()
        mgr.set("recording.fps", 120, auto_save=True)
        # Reload from file
        mgr2 = ConfigManager(config_file=self.config_path)
        self.assertEqual(mgr2.get("recording.fps"), 120)

    def test_get_network_config(self):
        mgr = self._make_manager()
        net = mgr.get_network_config()
        self.assertIsInstance(net, dict)
        self.assertIn("artnet_ip", net)

    def test_get_recording_config(self):
        mgr = self._make_manager()
        rec = mgr.get_recording_config()
        self.assertIn("fps", rec)

    def test_get_ui_config(self):
        mgr = self._make_manager()
        ui = mgr.get_ui_config()
        self.assertIn("theme", ui)

    def test_reset_to_defaults(self):
        mgr = self._make_manager()
        mgr.set("recording.fps", 1, auto_save=True)
        mgr.reset_to_defaults()
        self.assertEqual(mgr.get("recording.fps"), 60)

    def test_repr(self):
        mgr = self._make_manager()
        r = repr(mgr)
        self.assertIn("ConfigManager", r)
        self.assertIn(CONFIG_VERSION, r)


class TestConfigManagerBackupRestore(unittest.TestCase):
    """Backup and restore functionality"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_path = Path(self.tmpdir) / "test_config.json"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_backup_creates_file(self):
        mgr = ConfigManager(config_file=self.config_path)
        backup = mgr.backup("test_suffix")
        self.assertIsNotNone(backup)
        self.assertTrue(backup.exists())

    def test_backup_default_suffix(self):
        mgr = ConfigManager(config_file=self.config_path)
        backup = mgr.backup()
        self.assertIsNotNone(backup)
        self.assertIn("config_backup_", backup.name)

    def test_restore_from_backup(self):
        mgr = ConfigManager(config_file=self.config_path)
        mgr.set("recording.fps", 99, auto_save=True)

        backup = mgr.backup("before_change")
        mgr.set("recording.fps", 1, auto_save=True)

        result = mgr.restore(backup)
        self.assertTrue(result)
        self.assertEqual(mgr.get("recording.fps"), 99)

    def test_restore_missing_file_fails(self):
        mgr = ConfigManager(config_file=self.config_path)
        result = mgr.restore(Path("/nonexistent/backup.json"))
        self.assertFalse(result)


class TestConfigManagerLicense(unittest.TestCase):
    """License key encryption (base64)"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_path = Path(self.tmpdir) / "test_config.json"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_set_get_license_key(self):
        mgr = ConfigManager(config_file=self.config_path)
        mgr.set_license_key("MY-SECRET-KEY", auto_save=False)
        result = mgr.get_license_key()
        self.assertEqual(result, "MY-SECRET-KEY")

    def test_license_key_is_base64_encoded(self):
        mgr = ConfigManager(config_file=self.config_path)
        mgr.set_license_key("test123", auto_save=False)
        raw = mgr.config.get("license", {}).get("key")
        # Verify it's base64
        decoded = base64.b64decode(raw.encode()).decode()
        self.assertEqual(decoded, "test123")

    def test_get_license_key_none(self):
        mgr = ConfigManager(config_file=self.config_path)
        # Default config has no license key
        result = mgr.get_license_key()
        # Could be None or decoded None
        self.assertIsNone(result)

    def test_update_license_info(self):
        mgr = ConfigManager(config_file=self.config_path)
        mgr.update_license_info("professional", "2026-12-31")
        self.assertEqual(mgr.get("license.type"), "professional")
        self.assertEqual(mgr.get("license.expires_at"), "2026-12-31")
        self.assertIsNotNone(mgr.get("license.activated_at"))


class TestConfigManagerMerge(unittest.TestCase):
    """Deep merge with defaults"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_path = Path(self.tmpdir) / "test_config.json"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_merge_adds_missing_keys(self):
        mgr = ConfigManager(config_file=self.config_path)
        partial = {"version": "2.0.0", "network": {"artnet_port": 6454}}
        result = mgr._merge_with_defaults(partial, DEFAULT_CONFIG)
        self.assertIn("ui", result)
        self.assertIn("recording", result)

    def test_merge_preserves_existing_values(self):
        mgr = ConfigManager(config_file=self.config_path)
        partial = {"version": "2.0.0", "network": {"artnet_port": 7000}}
        result = mgr._merge_with_defaults(partial, DEFAULT_CONFIG)
        self.assertEqual(result["network"]["artnet_port"], 7000)

    def test_merge_deep_nested(self):
        mgr = ConfigManager(config_file=self.config_path)
        partial = {"network": {"artnet_ip": "10.0.0.1"}}
        result = mgr._merge_with_defaults(partial, DEFAULT_CONFIG)
        self.assertEqual(result["network"]["artnet_ip"], "10.0.0.1")
        self.assertEqual(result["network"]["artnet_port"], 6454)  # default preserved


class TestConfigManagerExportImport(unittest.TestCase):
    """Export and import config"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_path = Path(self.tmpdir) / "test_config.json"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_export_creates_file(self):
        mgr = ConfigManager(config_file=self.config_path)
        export_path = Path(self.tmpdir) / "exported.json"
        result = mgr.export_config(export_path)
        self.assertTrue(result)
        self.assertTrue(export_path.exists())

        with open(export_path, 'r') as f:
            exported = json.load(f)
        self.assertEqual(exported["version"], CONFIG_VERSION)

    def test_import_valid_config(self):
        mgr = ConfigManager(config_file=self.config_path)

        # Create a valid config file to import
        import_path = Path(self.tmpdir) / "import.json"
        valid_cfg = {
            "version": "2.0.0",
            "network": {"artnet_ip": "10.0.0.1", "artnet_port": 6454,
                       "broadcast_ip": "255.255.255.255", "interface": "auto", "timeout": 5.0},
            "recording": {"fps": 30, "format": "binary", "auto_save": True,
                         "compression": True, "buffer_size": 100, "default_path": "shows"},
            "ui": {"theme": "light", "language": "en", "window_width": 1280,
                  "window_height": 720, "window_maximized": False,
                  "fps_display": True, "show_tooltips": True}
        }
        with open(import_path, 'w') as f:
            json.dump(valid_cfg, f)

        result = mgr.import_config(import_path)
        self.assertTrue(result)
        self.assertEqual(mgr.get("ui.theme"), "light")

    def test_import_invalid_config_fails(self):
        mgr = ConfigManager(config_file=self.config_path)

        import_path = Path(self.tmpdir) / "bad_import.json"
        bad_cfg = {
            "network": {"artnet_port": 80},  # Invalid port
            "recording": {"fps": 0, "format": "xml"},  # Invalid
            "ui": {"theme": "neon", "language": "fr", "window_width": 100, "window_height": 100}
        }
        with open(import_path, 'w') as f:
            json.dump(bad_cfg, f)

        result = mgr.import_config(import_path)
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()