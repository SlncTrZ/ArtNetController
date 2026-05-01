"""test_network_utils — Unit tests cho Network Utilities.

Tests: IP validation, adapter detection, primary IP fallback.

Wing: code_chronicles
Topic: unit_testing
Last Updated: 2026-05-01 23:35
"""

import socket
import unittest
from unittest.mock import patch, MagicMock

from src.utils.network_utils import (
    get_network_adapters,
    get_primary_ip,
    validate_ip_address,
)


class TestValidateIPAddress(unittest.TestCase):
    """IP address validation tests"""

    def test_valid_ipv4_localhost(self):
        self.assertTrue(validate_ip_address("127.0.0.1"))

    def test_valid_ipv4_private(self):
        self.assertTrue(validate_ip_address("192.168.1.100"))

    def test_valid_ipv4_broadcast_zero(self):
        self.assertTrue(validate_ip_address("0.0.0.0"))

    def test_valid_ipv4_public(self):
        self.assertTrue(validate_ip_address("8.8.8.8"))

    def test_valid_ipv4_class_a(self):
        self.assertTrue(validate_ip_address("10.0.0.1"))

    def test_valid_ipv4_class_b(self):
        self.assertTrue(validate_ip_address("172.16.0.1"))

    def test_invalid_empty(self):
        self.assertFalse(validate_ip_address(""))

    def test_invalid_hostname(self):
        self.assertFalse(validate_ip_address("google.com"))

    def test_invalid_out_of_range(self):
        self.assertFalse(validate_ip_address("256.0.0.1"))

    def test_invalid_negative(self):
        self.assertFalse(validate_ip_address("-1.0.0.1"))

    def test_invalid_extra_octets(self):
        self.assertFalse(validate_ip_address("1.2.3.4.5"))

    def test_invalid_missing_octets(self):
        # Note: socket.inet_aton accepts "1.2.3" as "1.2.0.3" (BSD compat)
        # So we test with truly invalid format
        self.assertFalse(validate_ip_address("1.2."))

    def test_invalid_letters(self):
        self.assertFalse(validate_ip_address("abc.def.ghi.jkl"))


class TestGetPrimaryIP(unittest.TestCase):
    """Primary IP detection tests"""

    def test_returns_string(self):
        result = get_primary_ip()
        self.assertIsInstance(result, str)

    def test_returns_valid_ip(self):
        result = get_primary_ip()
        self.assertTrue(validate_ip_address(result))

    @patch('src.utils.network_utils.socket.socket')
    def test_socket_method(self, mock_socket_cls):
        """Uses UDP socket trick to detect primary IP"""
        mock_sock = MagicMock()
        mock_sock.getsockname.return_value = ("192.168.1.50", 12345)
        mock_socket_cls.return_value = mock_sock

        result = get_primary_ip()
        self.assertEqual(result, "192.168.1.50")
        mock_sock.connect.assert_called_once_with(("8.8.8.8", 80))
        mock_sock.close.assert_called_once()

    @patch('src.utils.network_utils.socket.socket')
    def test_fallback_on_error(self, mock_socket_cls):
        """Returns 127.0.0.1 when socket fails"""
        mock_socket_cls.side_effect = OSError("No network")
        result = get_primary_ip()
        self.assertEqual(result, "127.0.0.1")

    @patch('src.utils.network_utils.socket.socket')
    def test_fallback_on_loopback(self, mock_socket_cls):
        """Returns 127.0.0.1 when primary is loopback"""
        mock_sock = MagicMock()
        mock_sock.getsockname.return_value = ("127.0.0.1", 12345)
        mock_socket_cls.return_value = mock_sock
        result = get_primary_ip()
        self.assertEqual(result, "127.0.0.1")


class TestGetNetworkAdapters(unittest.TestCase):
    """Network adapter detection tests"""

    def test_returns_dict(self):
        result = get_network_adapters()
        self.assertIsInstance(result, dict)

    def test_always_has_loopback(self):
        result = get_network_adapters()
        has_loopback = any("127.0.0.1" in v for v in result.values())
        self.assertTrue(has_loopback, f"Should have loopback, got: {result}")

    def test_has_at_least_two_adapters(self):
        """With psutil, returns all system adapters; without, returns primary + loopback + broadcast"""
        result = get_network_adapters()
        self.assertGreaterEqual(len(result), 2, f"Should have >= 2 adapters, got: {result}")

    def test_all_values_are_valid_ips(self):
        result = get_network_adapters()
        for name, ip in result.items():
            self.assertTrue(validate_ip_address(ip),
                          f"Adapter '{name}' has invalid IP: {ip}")

    def test_non_empty(self):
        result = get_network_adapters()
        self.assertGreater(len(result), 0)

    @patch('src.utils.network_utils.socket.gethostbyname')
    @patch('src.utils.network_utils.socket.gethostname')
    def test_fallback_without_psutil(self, mock_hostname, mock_gethost):
        """Fallback works without psutil"""
        mock_hostname.return_value = "test-pc"
        mock_gethost.return_value = "192.168.1.100"

        with patch.dict('sys.modules', {'psutil': None}):
            result = get_network_adapters()
            ips = list(result.values())
            self.assertIn("192.168.1.100", ips)
            self.assertIn("127.0.0.1", ips)


if __name__ == '__main__':
    unittest.main()