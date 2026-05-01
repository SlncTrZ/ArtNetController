"""test_serial.py — Unit tests for serial module (IOBoard Protocol, Port Scanner, Serial Controller).

Tests DMX packet pack/unpack, checksum, port scanning with mock data,
auto-mapping logic, and serial controller with mock ports.

Topic: testing
Last Updated: 2026-05-01 23:45
"""

import pytest
import struct
from unittest.mock import patch, MagicMock, PropertyMock
from dataclasses import dataclass

from src.serial.ioboard_protocol import DMXPacket, IOBoardProtocol
from src.serial.port_scanner import PortScanner, IOBoardInfo
from src.serial.serial_controller import SerialController, BoardConnection


# ─── DMXPacket Tests ─────────────────────────────────────────────────────

class TestDMXPacketInit:
    """DMXPacket initialization and validation"""

    def test_valid_universe_zero(self):
        pkt = DMXPacket(0, bytes(512))
        assert pkt.universe == 0

    def test_valid_universe_255(self):
        pkt = DMXPacket(255, bytes(512))
        assert pkt.universe == 255

    def test_invalid_universe_negative(self):
        with pytest.raises(ValueError, match="0-255"):
            DMXPacket(-1, bytes(512))

    def test_invalid_universe_256(self):
        with pytest.raises(ValueError, match="0-255"):
            DMXPacket(256, bytes(512))

    def test_data_padded_short(self):
        """Short data gets padded with zeros"""
        pkt = DMXPacket(0, bytes(10))
        assert len(pkt.dmx_data) == 512
        assert pkt.dmx_data[:10] == bytes(10)

    def test_data_truncated_long(self):
        """Data longer than 512 gets truncated"""
        pkt = DMXPacket(0, bytes(600))
        assert len(pkt.dmx_data) == 512

    def test_data_exact_512(self):
        data = bytes(range(256)) + bytes(range(256))
        pkt = DMXPacket(0, data)
        assert len(pkt.dmx_data) == 512


class TestDMXPacketPack:
    """DMXPacket.pack() byte format"""

    def test_header_bytes(self):
        pkt = DMXPacket(0, bytes(512))
        raw = pkt.pack()
        assert raw[0] == 0xAA
        assert raw[1] == 0x55

    def test_universe_byte(self):
        pkt = DMXPacket(42, bytes(512))
        raw = pkt.pack()
        assert raw[2] == 42

    def test_length_field_big_endian(self):
        pkt = DMXPacket(0, bytes(512))
        raw = pkt.pack()
        length = struct.unpack('>H', raw[3:5])[0]
        assert length == 512

    def test_total_packet_size(self):
        pkt = DMXPacket(0, bytes(512))
        assert len(pkt.pack()) == 518  # Header(2)+Universe(1)+Length(2)+Data(512)+Checksum(1)

    def test_checksum_xor(self):
        """Checksum = XOR of all bytes before checksum"""
        pkt = DMXPacket(0, bytes(512))
        raw = pkt.pack()
        expected = 0
        for b in raw[:-1]:
            expected ^= b
        assert raw[-1] == expected

    def test_different_universes_different_packets(self):
        p1 = DMXPacket(0, bytes(512)).pack()
        p2 = DMXPacket(1, bytes(512)).pack()
        assert p1 != p2


class TestDMXPacketUnpack:
    """DMXPacket.unpack() parsing and validation"""

    def test_roundtrip(self):
        """pack → unpack yields same data"""
        original_data = bytes(range(256)) + bytes(256)
        packed = DMXPacket(5, original_data).pack()
        pkt = DMXPacket.unpack(packed)
        assert pkt is not None
        assert pkt.universe == 5
        assert pkt.dmx_data == original_data

    def test_unpack_wrong_size(self):
        result = DMXPacket.unpack(bytes(100))
        assert result is None

    def test_unpack_bad_header(self):
        data = bytearray(DMXPacket(0, bytes(512)).pack())
        data[0] = 0x00  # Corrupt header
        assert DMXPacket.unpack(bytes(data)) is None

    def test_unpack_bad_checksum(self):
        data = bytearray(DMXPacket(0, bytes(512)).pack())
        data[-1] ^= 0xFF  # Flip checksum
        assert DMXPacket.unpack(bytes(data)) is None

    def test_unpack_valid_full_channel_data(self):
        """All channels at 255"""
        data = bytes([0xFF] * 512)
        packed = DMXPacket(10, data).pack()
        pkt = DMXPacket.unpack(packed)
        assert pkt is not None
        assert all(b == 0xFF for b in pkt.dmx_data)


# ─── IOBoardProtocol Tests ───────────────────────────────────────────────

class TestIOBoardProtocol:
    """IOBoardProtocol utility methods"""

    def test_create_packet_returns_bytes(self):
        result = IOBoardProtocol.create_packet(0, bytes(512))
        assert isinstance(result, bytes)
        assert len(result) == 518

    def test_verify_packet_valid(self):
        packed = IOBoardProtocol.create_packet(0, bytes(512))
        assert IOBoardProtocol.verify_packet(packed) is True

    def test_verify_packet_invalid(self):
        assert IOBoardProtocol.verify_packet(bytes(517)) is False

    def test_transmission_time_500000(self):
        """~10.34ms at 500000 baud"""
        ms = IOBoardProtocol.calculate_transmission_time(500000)
        assert 9.0 < ms < 12.0

    def test_transmission_time_115200(self):
        """Slower baudrate = longer time"""
        ms = IOBoardProtocol.calculate_transmission_time(115200)
        assert ms > 40.0

    def test_max_refresh_rate(self):
        rate = IOBoardProtocol.get_max_refresh_rate(500000)
        assert rate > 0
        assert 80.0 < rate < 120.0

    def test_recommended_baudrate(self):
        assert IOBoardProtocol.get_recommended_baudrate() == 500000


# ─── PortScanner Tests (with mock) ──────────────────────────────────────

class TestPortScannerParsing:
    """PortScanner._parse_port_info with mock port info"""

    def _make_port_info(self, device="COM3", description="", manufacturer="",
                        vid=None, pid=None, serial_number=None):
        """Create a mock port info object"""
        mock = MagicMock()
        mock.device = device
        mock.description = description
        mock.manufacturer = manufacturer
        mock.vid = vid
        mock.pid = pid
        mock.serial_number = serial_number
        mock.hwid = "USB\\VID_1234&PID_5678"
        return mock

    def test_detect_board_standard_name(self):
        info = self._make_port_info(description="DMX Master IO #1")
        result = PortScanner._parse_port_info(info)
        assert result is not None
        assert result.board_number == 1
        assert result.port == "COM3"

    def test_detect_board_number_5(self):
        info = self._make_port_info(description="DMX Master IO #5")
        result = PortScanner._parse_port_info(info)
        assert result is not None
        assert result.board_number == 5

    def test_detect_alt_pattern_nohash(self):
        info = self._make_port_info(description="DMXMaster IO 3")
        result = PortScanner._parse_port_info(info)
        assert result is not None
        assert result.board_number == 3

    def test_detect_alt_pattern_dash(self):
        info = self._make_port_info(description="DMX-Master-IO-2")
        result = PortScanner._parse_port_info(info)
        assert result is not None
        assert result.board_number == 2

    def test_not_ioboard_random_device(self):
        info = self._make_port_info(description="Arduino Uno")
        result = PortScanner._parse_port_info(info)
        assert result is None

    def test_not_ioboard_empty(self):
        info = self._make_port_info(description="")
        result = PortScanner._parse_port_info(info)
        assert result is None

    def test_vid_pid_extracted(self):
        info = self._make_port_info(
            description="DMX Master IO #1",
            vid=0x1234, pid=0x5678
        )
        result = PortScanner._parse_port_info(info)
        assert result.vid == 0x1234
        assert result.pid == 0x5678

    def test_serial_number_extracted(self):
        info = self._make_port_info(
            description="DMX Master IO #1",
            serial_number="ABC123"
        )
        result = PortScanner._parse_port_info(info)
        assert result.serial_number == "ABC123"

    def test_repr_format(self):
        board = IOBoardInfo(
            port="COM3", device_name="DMX Master IO #1",
            board_number=1, description="test",
            vid=None, pid=None, serial_number=None, manufacturer=None
        )
        assert "Board #1" in repr(board)
        assert "COM3" in repr(board)

    def test_sorting_by_board_number(self):
        b2 = IOBoardInfo("COM4", "DMX Master IO #2", 2, "", None, None, None, None)
        b1 = IOBoardInfo("COM3", "DMX Master IO #1", 1, "", None, None, None, None)
        assert sorted([b2, b1]) == [b1, b2]


class TestPortScannerScanMocked:
    """PortScanner.scan_ports with mocked pyserial"""

    def _make_port_info(self, description, device="COM3"):
        mock = MagicMock()
        mock.device = device
        mock.description = description
        mock.manufacturer = ""
        mock.vid = None
        mock.pid = None
        mock.serial_number = None
        mock.hwid = ""
        return mock

    @patch('src.serial.port_scanner.PYSERIAL_AVAILABLE', True)
    def test_scan_finds_boards(self):
        """Test scan orchestration by mocking _parse_port_info"""
        board1 = IOBoardInfo("COM3", "DMX Master IO #1", 1, "DMX Master IO #1", None, None, None, None)
        board2 = IOBoardInfo("COM4", "DMX Master IO #2", 2, "DMX Master IO #2", None, None, None, None)

        with patch.object(PortScanner, '_parse_port_info', side_effect=[board1, board2]), \
             patch.object(PortScanner, '_get_comports', return_value=[MagicMock(), MagicMock()]):
            boards = PortScanner.scan_ports()
            assert len(boards) == 2
            assert boards[0].board_number == 1
            assert boards[1].board_number == 2

    @patch('src.serial.port_scanner.PYSERIAL_AVAILABLE', True)
    def test_scan_no_boards(self):
        with patch.object(PortScanner, '_get_comports', return_value=[]):
            boards = PortScanner.scan_ports()
            assert boards == []

    @patch.object(PortScanner, 'is_available', return_value=False)
    def test_scan_no_pyserial(self, mock_avail):
        boards = PortScanner.scan_ports()
        assert boards == []


# ─── SerialController Tests (with mock serial) ───────────────────────────

class TestSerialControllerAutoMapping:
    """Auto-mapping: Board #N → Universe [(N-1)*2, (N-1)*2+1]"""

    def _make_controller_with_boards(self, board_numbers):
        """Create controller with mock connected boards"""
        ctrl = SerialController.__new__(SerialController)
        ctrl.baudrate = 500000
        ctrl.running = False
        ctrl.connections = {}
        ctrl.universe_to_board = {}
        ctrl.auto_mapping_enabled = True
        ctrl.manual_mapping = {}
        ctrl.connections_lock = MagicMock()
        ctrl.connection_status_callback = None
        ctrl.error_callback = None
        ctrl.total_packets_sent = 0
        ctrl.total_errors = 0
        ctrl._license_manager = None

        for bn in board_numbers:
            board_info = IOBoardInfo(
                port=f"COM{bn+2}", device_name=f"DMX Master IO #{bn}",
                board_number=bn, description="test",
                vid=None, pid=None, serial_number=None, manufacturer=None
            )
            mock_port = MagicMock()
            ctrl.connections[bn] = BoardConnection(
                board_info=board_info, port=mock_port,
                universes=[], packets_sent=0, errors=0,
                last_send_time=0, connected=True
            )

        # Make lock a real context manager
        import threading
        ctrl.connections_lock = threading.Lock()
        return ctrl

    def test_board1_maps_universe_0_1(self):
        ctrl = self._make_controller_with_boards([1])
        ctrl.apply_auto_mapping()
        assert ctrl.get_board_for_universe(0) == 1
        assert ctrl.get_board_for_universe(1) == 1

    def test_board2_maps_universe_2_3(self):
        ctrl = self._make_controller_with_boards([1, 2])
        ctrl.apply_auto_mapping()
        assert ctrl.get_board_for_universe(2) == 2
        assert ctrl.get_board_for_universe(3) == 2

    def test_board3_maps_universe_4_5(self):
        ctrl = self._make_controller_with_boards([1, 2, 3])
        ctrl.apply_auto_mapping()
        assert ctrl.get_board_for_universe(4) == 3
        assert ctrl.get_board_for_universe(5) == 3

    def test_unmapped_universe_returns_none(self):
        ctrl = self._make_controller_with_boards([1])
        ctrl.apply_auto_mapping()
        assert ctrl.get_board_for_universe(99) is None

    def test_auto_mapping_disabled(self):
        ctrl = self._make_controller_with_boards([1])
        ctrl.auto_mapping_enabled = False
        ctrl.apply_auto_mapping()
        assert ctrl.get_board_for_universe(0) is None

    def test_get_universe_mapping(self):
        ctrl = self._make_controller_with_boards([1, 2])
        ctrl.apply_auto_mapping()
        mapping = ctrl.get_universe_mapping()
        assert mapping[1] == [0, 1]
        assert mapping[2] == [2, 3]


class TestSerialControllerManualMapping:
    """Manual universe mapping override"""

    def _make_controller_with_board(self, board_number=1):
        ctrl = SerialController.__new__(SerialController)
        ctrl.baudrate = 500000
        ctrl.running = False
        ctrl.connections = {}
        ctrl.universe_to_board = {}
        ctrl.auto_mapping_enabled = True
        ctrl.manual_mapping = {}
        ctrl.connection_status_callback = None
        ctrl.error_callback = None
        ctrl.total_packets_sent = 0
        ctrl.total_errors = 0
        ctrl._license_manager = None

        board_info = IOBoardInfo(
            port="COM3", device_name=f"DMX Master IO #{board_number}",
            board_number=board_number, description="test",
            vid=None, pid=None, serial_number=None, manufacturer=None
        )
        import threading
        ctrl.connections_lock = threading.Lock()
        ctrl.connections[board_number] = BoardConnection(
            board_info=board_info, port=MagicMock(),
            universes=[], packets_sent=0, errors=0,
            last_send_time=0, connected=True
        )
        return ctrl

    def test_manual_mapping_single_universe(self):
        ctrl = self._make_controller_with_board(1)
        ctrl.set_manual_mapping(1, [10])
        assert ctrl.get_board_for_universe(10) == 1

    def test_manual_mapping_overrides_auto(self):
        ctrl = self._make_controller_with_board(1)
        ctrl.apply_auto_mapping()
        assert ctrl.get_board_for_universe(0) == 1
        ctrl.set_manual_mapping(1, [20, 21])
        assert ctrl.get_board_for_universe(20) == 1
        assert ctrl.get_board_for_universe(21) == 1
        assert ctrl.get_board_for_universe(0) is None  # Removed old

    def test_manual_mapping_nonexistent_board(self):
        ctrl = self._make_controller_with_board(1)
        ctrl.set_manual_mapping(99, [0])  # Should not raise
        assert ctrl.get_board_for_universe(0) is None


class TestSerialControllerSendDMX:
    """send_dmx with mock serial port"""

    def _make_controller_with_board(self, board_number=1):
        ctrl = SerialController.__new__(SerialController)
        ctrl.baudrate = 500000
        ctrl.running = False
        ctrl.connections = {}
        ctrl.universe_to_board = {}
        ctrl.auto_mapping_enabled = True
        ctrl.manual_mapping = {}
        ctrl.connection_status_callback = None
        ctrl.error_callback = None
        ctrl.total_packets_sent = 0
        ctrl.total_errors = 0
        ctrl._license_manager = None

        board_info = IOBoardInfo(
            port="COM3", device_name=f"DMX Master IO #{board_number}",
            board_number=board_number, description="test",
            vid=None, pid=None, serial_number=None, manufacturer=None
        )
        import threading
        ctrl.connections_lock = threading.Lock()
        mock_port = MagicMock()
        ctrl.connections[board_number] = BoardConnection(
            board_info=board_info, port=mock_port,
            universes=[0, 1], packets_sent=0, errors=0,
            last_send_time=0, connected=True
        )
        ctrl.universe_to_board = {0: board_number, 1: board_number}
        return ctrl, mock_port

    def test_send_dmx_success(self):
        ctrl, mock_port = self._make_controller_with_board(1)
        result = ctrl.send_dmx(0, bytes(512))
        assert result is True
        mock_port.write.assert_called_once()
        assert ctrl.total_packets_sent == 1

    def test_send_dmx_unmapped_universe(self):
        ctrl, _ = self._make_controller_with_board(1)
        result = ctrl.send_dmx(99, bytes(512))
        assert result is False
        assert ctrl.total_packets_sent == 0

    def test_send_dmx_updates_connection_stats(self):
        ctrl, _ = self._make_controller_with_board(1)
        ctrl.send_dmx(0, bytes(512))
        conn = ctrl.connections[1]
        assert conn.packets_sent == 1

    def test_send_dmx_write_error_increments_errors(self):
        ctrl, mock_port = self._make_controller_with_board(1)
        mock_port.write.side_effect = OSError("Port error")
        # Suppress reconnect thread
        with patch.object(ctrl, '_reconnect_board'):
            result = ctrl.send_dmx(0, bytes(512))
        assert result is False
        assert ctrl.total_errors == 1

    def test_send_dmx_creates_517_byte_packet(self):
        ctrl, mock_port = self._make_controller_with_board(1)
        ctrl.send_dmx(0, bytes(512))
        written = mock_port.write.call_args[0][0]
        assert len(written) == 518


class TestSerialControllerStatistics:
    """Statistics and status methods"""

    def _make_controller(self):
        ctrl = SerialController.__new__(SerialController)
        ctrl.baudrate = 500000
        ctrl.running = False
        ctrl.connections = {}
        ctrl.universe_to_board = {}
        ctrl.auto_mapping_enabled = True
        ctrl.manual_mapping = {}
        ctrl.connection_status_callback = None
        ctrl.error_callback = None
        ctrl.total_packets_sent = 10
        ctrl.total_errors = 1
        ctrl._license_manager = None

        import threading
        ctrl.connections_lock = threading.Lock()
        return ctrl

    def test_is_connected_false_when_empty(self):
        ctrl = self._make_controller()
        assert ctrl.is_connected() is False

    def test_get_connection_count_zero(self):
        ctrl = self._make_controller()
        assert ctrl.get_connection_count() == 0

    def test_get_connected_boards_empty(self):
        ctrl = self._make_controller()
        assert ctrl.get_connected_boards() == []

    def test_get_board_info_none_when_not_connected(self):
        ctrl = self._make_controller()
        assert ctrl.get_board_info(1) is None

    def test_get_board_statistics_none_when_not_connected(self):
        ctrl = self._make_controller()
        assert ctrl.get_board_statistics(1) is None

    def test_get_all_statistics_structure(self):
        ctrl = self._make_controller()
        stats = ctrl.get_all_statistics()
        assert 'total_boards' in stats
        assert 'total_packets_sent' in stats
        assert 'total_errors' in stats
        assert 'universe_mapping' in stats
        assert 'auto_mapping_enabled' in stats