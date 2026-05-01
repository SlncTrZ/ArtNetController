"""test_dmx_recorder — Unit tests cho Binary DMX Recorder V2.0.

Tests: binary format read/write, CRC16 validation, frame integrity,
      recording lifecycle, playback buffering.

Wing: code_chronicles
Topic: unit_testing
Last Updated: 2026-05-01 23:21
"""

import os
import struct
import tempfile
import time
import unittest
from pathlib import Path

# Add project root to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.show.dmx_recorder import (
    DMXFrame, DMXRecorder, DMXPlayer,
    MAGIC_BYTES, FORMAT_VERSION, HEADER_SIZE, FRAME_SIZE,
    DMX_CHANNELS, FLAG_HAS_CRC, FLAG_MONOTONIC_TIME,
    crc16_modbus, verify_recording,
)


class TestCRC16(unittest.TestCase):
    """CRC-16/MODBUS checksum tests"""

    def test_crc_empty_data(self):
        """CRC of empty bytes should be 0xFFFF"""
        result = crc16_modbus(b'')
        self.assertEqual(result, 0xFFFF)

    def test_crc_known_value(self):
        """CRC of known data matches expected value"""
        # MODBUS CRC for "123456789" is well-documented
        result = crc16_modbus(b'123456789')
        self.assertEqual(result, 0x4B37)

    def test_crc_deterministic(self):
        """Same input always produces same CRC"""
        data = bytes(i % 256 for i in range(512))
        crc1 = crc16_modbus(data)
        crc2 = crc16_modbus(data)
        self.assertEqual(crc1, crc2)

    def test_crc_different_data(self):
        """Different inputs produce different CRCs"""
        data1 = bytes([0] * 512)
        data2 = bytes([1] * 512)
        self.assertNotEqual(crc16_modbus(data1), crc16_modbus(data2))


class TestDMXFrame(unittest.TestCase):
    """DMX Frame serialization/deserialization tests"""

    def test_frame_creation(self):
        """Frame creates with correct defaults"""
        data = bytes([255] * 512)
        frame = DMXFrame(1.0, 0, data)
        self.assertEqual(frame.timestamp, 1.0)
        self.assertEqual(frame.universe, 0)
        self.assertEqual(len(frame.data), 512)
        self.assertIsNotNone(frame.crc)

    def test_frame_padding_short_data(self):
        """Data shorter than 512 bytes gets padded on serialization"""
        data = bytes([128] * 100)
        frame = DMXFrame(0.0, 1, data)
        # frame.data stores original; padding happens in to_bytes()
        self.assertEqual(len(frame.data), 100)
        raw = frame.to_bytes()
        self.assertEqual(len(raw), FRAME_SIZE)  # 524 = full padded frame

    def test_frame_truncation_long_data(self):
        """Data longer than 512 bytes gets truncated"""
        data = bytes([200] * 600)
        frame = DMXFrame(0.0, 1, data)
        self.assertEqual(len(frame.data), 512)

    def test_frame_to_bytes_size(self):
        """Serialized frame is exactly FRAME_SIZE bytes"""
        frame = DMXFrame(1.5, 2, bytes(i % 256 for i in range(512)))
        raw = frame.to_bytes()
        self.assertEqual(len(raw), FRAME_SIZE)

    def test_frame_roundtrip(self):
        """Frame survives serialize → deserialize cycle"""
        original = DMXFrame(2.5, 5, bytes(i % 256 for i in range(512)))
        raw = original.to_bytes()
        restored = DMXFrame.from_bytes(raw, validate=True)
        self.assertIsNotNone(restored)
        self.assertEqual(restored.timestamp, original.timestamp)
        self.assertEqual(restored.universe, original.universe)
        self.assertEqual(restored.data, original.data)
        self.assertEqual(restored.crc, original.crc)

    def test_frame_crc_validation_valid(self):
        """Valid frame passes CRC check"""
        frame = DMXFrame(0.0, 0, bytes(512))
        self.assertTrue(frame.validate_crc())

    def test_frame_crc_validation_corrupted(self):
        """Corrupted frame fails CRC check"""
        frame = DMXFrame(0.0, 0, bytes(512))
        raw = bytearray(frame.to_bytes())
        # Corrupt a byte in the DMX data section
        raw[20] ^= 0xFF
        restored = DMXFrame.from_bytes(bytes(raw), validate=True)
        self.assertIsNone(restored)  # Should fail CRC

    def test_frame_from_bytes_too_short(self):
        """Too-short data returns None"""
        result = DMXFrame.from_bytes(b'\x00' * 10)
        self.assertIsNone(result)

    def test_frame_pack_format(self):
        """Frame binary format: >d H 512s H"""
        frame = DMXFrame(1.0, 3, bytes(512))
        raw = frame.to_bytes()
        # Unpack manually to verify format
        ts, uni, dmx, crc = struct.unpack('>d H 512s H', raw[:FRAME_SIZE])
        self.assertEqual(ts, 1.0)
        self.assertEqual(uni, 3)
        self.assertEqual(crc, frame.crc)


class TestDMXRecorder(unittest.TestCase):
    """Recording lifecycle tests"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.filepath = os.path.join(self.tmpdir, "test.dmxrec")

    def tearDown(self):
        if os.path.exists(self.filepath):
            os.unlink(self.filepath)
        os.rmdir(self.tmpdir)

    def test_start_recording_creates_file(self):
        """start_recording() creates the output file"""
        recorder = DMXRecorder(self.filepath)
        result = recorder.start_recording(fps=40.0)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.filepath))
        recorder.stop_recording()

    def test_record_and_stop(self):
        """Recording frames then stopping returns valid stats"""
        recorder = DMXRecorder(self.filepath)
        recorder.start_recording(fps=40.0)

        for i in range(10):
            dmx = bytes([(i + j) % 256 for j in range(512)])
            recorder.write_frame(0, dmx)

        stats = recorder.stop_recording()
        self.assertIsNotNone(stats)
        self.assertEqual(stats['frame_count'], 10)
        self.assertEqual(stats['format_version'], FORMAT_VERSION)
        self.assertTrue(stats['has_crc'])
        self.assertIn(0, stats['universes'])

    def test_write_without_start_fails(self):
        """write_frame() before start_recording() returns False"""
        recorder = DMXRecorder(self.filepath)
        result = recorder.write_frame(0, bytes(512))
        self.assertFalse(result)

    def test_file_size_calculation(self):
        """File size = HEADER_SIZE + N * FRAME_SIZE"""
        recorder = DMXRecorder(self.filepath)
        recorder.start_recording(fps=40.0)

        n_frames = 20
        for i in range(n_frames):
            recorder.write_frame(i % 2, bytes(512))

        recorder.stop_recording()

        expected_size = HEADER_SIZE + n_frames * FRAME_SIZE
        actual_size = os.path.getsize(self.filepath)
        self.assertEqual(actual_size, expected_size)


class TestDMXPlayer(unittest.TestCase):
    """Playback and file reading tests"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.filepath = os.path.join(self.tmpdir, "test_playback.dmxrec")
        # Create a test recording
        self._create_test_recording(30, fps=40.0)

    def _create_test_recording(self, n_frames: int, fps: float = 40.0):
        recorder = DMXRecorder(self.filepath)
        recorder.start_recording(fps=fps)
        for i in range(n_frames):
            dmx = bytes([(i + j) % 256 for j in range(512)])
            recorder.write_frame(i % 3, dmx)  # Universes 0, 1, 2
        self.stats = recorder.stop_recording()

    def tearDown(self):
        if os.path.exists(self.filepath):
            os.unlink(self.filepath)
        os.rmdir(self.tmpdir)

    def test_open_and_read_header(self):
        """Player reads header correctly"""
        with DMXPlayer(self.filepath) as player:
            info = player.get_info()
            self.assertEqual(info['version'], FORMAT_VERSION)
            self.assertEqual(info['frame_count'], 30)
            self.assertEqual(info['fps'], 40.0)
            self.assertTrue(info['has_crc'])

    def test_read_all_frames(self):
        """Player reads all frames from file"""
        with DMXPlayer(self.filepath) as player:
            frames = player.read_all_frames()
            self.assertEqual(len(frames), 30)

    def test_seek_and_read(self):
        """Player can seek to specific frame"""
        with DMXPlayer(self.filepath) as player:
            # Seek to frame 15
            result = player.seek_frame(15)
            self.assertTrue(result)
            frame = player.read_frame()
            self.assertIsNotNone(frame)
            self.assertEqual(player.current_frame_index, 16)

    def test_seek_out_of_range(self):
        """Seeking out of range returns False"""
        with DMXPlayer(self.filepath) as player:
            result = player.seek_frame(999)
            self.assertFalse(result)

    def test_get_frame_at_time(self):
        """Time-based frame lookup works"""
        with DMXPlayer(self.filepath) as player:
            # Get frame near t=0
            frame = player.get_frame_at_time(0.0)
            self.assertIsNotNone(frame)
            self.assertAlmostEqual(frame.timestamp, 0.0, places=1)

    def test_verify_recording(self):
        """verify_recording() reports all frames valid"""
        stats = verify_recording(self.filepath)
        self.assertEqual(stats['total_frames'], 30)
        self.assertEqual(stats['crc_errors'], 0)
        self.assertEqual(stats['valid_frames'], 30)

    def test_file_not_found(self):
        """Opening non-existent file returns False"""
        player = DMXPlayer("/nonexistent/path/file.dmxrec")
        result = player.open()
        self.assertFalse(result)


class TestBinaryFormatV2(unittest.TestCase):
    """Binary format V2.0 specification compliance tests"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.filepath = os.path.join(self.tmpdir, "format_test.dmxrec")

    def tearDown(self):
        if os.path.exists(self.filepath):
            os.unlink(self.filepath)
        os.rmdir(self.tmpdir)

    def test_header_magic_bytes(self):
        """File starts with 'DMXR' magic bytes"""
        recorder = DMXRecorder(self.filepath)
        recorder.start_recording(fps=44.0)
        recorder.write_frame(0, bytes(512))
        recorder.stop_recording()

        with open(self.filepath, 'rb') as f:
            magic = f.read(4)
        self.assertEqual(magic, MAGIC_BYTES)

    def test_header_version(self):
        """Header byte 4 is FORMAT_VERSION (2)"""
        recorder = DMXRecorder(self.filepath)
        recorder.start_recording(fps=44.0)
        recorder.write_frame(0, bytes(512))
        recorder.stop_recording()

        with open(self.filepath, 'rb') as f:
            f.read(4)  # skip magic
            version = struct.unpack('B', f.read(1))[0]
        self.assertEqual(version, FORMAT_VERSION)
        self.assertEqual(version, 2)

    def test_header_flags(self):
        """Header flags include CRC and Monotonic Time"""
        recorder = DMXRecorder(self.filepath)
        recorder.start_recording(fps=44.0)
        recorder.write_frame(0, bytes(512))
        recorder.stop_recording()

        with open(self.filepath, 'rb') as f:
            header = f.read(HEADER_SIZE)

        # Parse header: >4s B H H I B 18s
        _, _, _, _, _, flags, _ = struct.unpack('>4s B H H I B 18s', header)
        self.assertTrue(flags & FLAG_HAS_CRC)
        self.assertTrue(flags & FLAG_MONOTONIC_TIME)

    def test_frame_size_is_524(self):
        """Each frame is exactly 524 bytes (8+2+512+2)"""
        self.assertEqual(FRAME_SIZE, 524)
        # 8 (timestamp float64) + 2 (universe uint16) + 512 (DMX) + 2 (CRC16)
        self.assertEqual(8 + 2 + 512 + 2, FRAME_SIZE)


if __name__ == '__main__':
    unittest.main()