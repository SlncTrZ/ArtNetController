"""test_artnet_controller — Unit tests cho Art-Net Protocol Implementation.

Tests: packet pack/unpack, DMX encoding, Poll encoding, header validation,
      universe validation, sequence counter.

Wing: code_chronicles
Topic: unit_testing
Last Updated: 2026-05-01 23:28
"""

import struct
import unittest

from src.artnet.controller import (
    ArtNetPacket, ArtNetPoll, ArtNetDMX, ArtNetController,
    ARTNET_PORT, RECV_BUFFER_SIZE, NODE_TIMEOUT_SEC,
)


class TestArtNetPacket(unittest.TestCase):
    """ArtNetPacket base class tests"""

    def test_header_is_correct(self):
        """Art-Net header is 'Art-Net\\x00' (8 bytes)"""
        self.assertEqual(ArtNetPacket.ARTNET_HEADER, b"Art-Net\x00")
        self.assertEqual(len(ArtNetPacket.ARTNET_HEADER), 8)

    def test_opcodes_are_valid(self):
        """OpCodes match Art-Net 4 specification"""
        self.assertEqual(ArtNetPacket.ARTNET_POLL, 0x2000)
        self.assertEqual(ArtNetPacket.ARTNET_POLL_REPLY, 0x2100)
        self.assertEqual(ArtNetPacket.ARTNET_DMX, 0x5000)
        self.assertEqual(ArtNetPacket.ARTNET_SYNC, 0x5200)
        self.assertEqual(ArtNetPacket.ARTNET_TIME_CODE, 0x9700)

    def test_pack_structure(self):
        """Pack produces: header(8) + opcode(2) + data"""
        pkt = ArtNetPacket()
        pkt.opcode = 0x5000
        pkt.data = b"\x01\x02"
        raw = pkt.pack()
        self.assertEqual(raw[:8], b"Art-Net\x00")
        self.assertEqual(struct.unpack('<H', raw[8:10])[0], 0x5000)
        self.assertEqual(raw[10:], b"\x01\x02")

    def test_unpack_valid_packet(self):
        """Unpack correctly parses valid Art-Net packet"""
        header = b"Art-Net\x00"
        opcode = struct.pack('<H', 0x5000)
        payload = b"\x00" * 100
        data = header + opcode + payload

        result = ArtNetPacket.unpack(data)
        self.assertIsNotNone(result)
        self.assertEqual(result['opcode'], 0x5000)
        self.assertEqual(result['payload'], payload)

    def test_unpack_too_short(self):
        """Unpack returns None for packets < 10 bytes"""
        self.assertIsNone(ArtNetPacket.unpack(b"Art-Net\x00"))
        self.assertIsNone(ArtNetPacket.unpack(b""))
        self.assertIsNone(ArtNetPacket.unpack(b"\x00" * 9))

    def test_unpack_wrong_header(self):
        """Unpack returns None for non-Art-Net packets"""
        data = b"DMX-Trash\x00" + b"\x00" * 20
        self.assertIsNone(ArtNetPacket.unpack(data))


class TestArtNetPoll(unittest.TestCase):
    """Art-Net Poll packet tests"""

    def test_poll_opcode(self):
        """Poll packet has OpCode 0x2000"""
        poll = ArtNetPoll()
        self.assertEqual(poll.opcode, ArtNetPacket.ARTNET_POLL)

    def test_poll_pack_size(self):
        """Poll packet = header(8) + opcode(2) + flags(1) + priority(1) = 12 bytes"""
        poll = ArtNetPoll()
        raw = poll.pack()
        self.assertEqual(len(raw), 12)

    def test_poll_flags_default(self):
        """Default flags = 0x06 (TalkToMe + Diagnostics)"""
        poll = ArtNetPoll()
        raw = poll.pack()
        flags = raw[10]
        priority = raw[11]
        self.assertEqual(flags, 0x06)
        self.assertEqual(priority, 0x00)


class TestArtNetDMX(unittest.TestCase):
    """Art-Net DMX packet tests"""

    def test_dmx_opcode(self):
        """DMX packet has OpCode 0x5000"""
        dmx = ArtNetDMX()
        self.assertEqual(dmx.opcode, ArtNetPacket.ARTNET_DMX)

    def test_dmx_default_512_channels(self):
        """Default DMX data is 512 zero bytes"""
        dmx = ArtNetDMX()
        self.assertEqual(len(dmx.dmx_data), 512)
        self.assertEqual(dmx.dmx_data, bytes(512))

    def test_dmx_pack_structure(self):
        """DMX pack: header(8) + opcode(2) + version(2) + seq(1) + phys(1) + universe(2) + length(2) + data"""
        dmx = ArtNetDMX(universe=1, sequence=42, dmx_data=bytes(128))
        raw = dmx.pack()

        # Minimum size: 8 + 2 + 2 + 1 + 1 + 2 + 2 + 128 = 146
        self.assertEqual(len(raw), 8 + 2 + 2 + 1 + 1 + 2 + 2 + 128)

        # Check header
        self.assertEqual(raw[:8], b"Art-Net\x00")

        # Check opcode (LE)
        opcode = struct.unpack('<H', raw[8:10])[0]
        self.assertEqual(opcode, 0x5000)

        # Check version (BE) = 14
        version = struct.unpack('>H', raw[10:12])[0]
        self.assertEqual(version, 14)

        # Check sequence
        self.assertEqual(raw[12], 42)

        # Check physical
        self.assertEqual(raw[13], 0)

        # Check universe (LE)
        universe = struct.unpack('<H', raw[14:16])[0]
        self.assertEqual(universe, 1)

        # Check length (BE)
        length = struct.unpack('>H', raw[16:18])[0]
        self.assertEqual(length, 128)

    def test_dmx_unpack_valid(self):
        """Unpack DMX payload correctly"""
        # Build a DMX payload (after header + opcode)
        dmx_data = bytes(i % 256 for i in range(512))
        payload = (
            struct.pack('>H', 14)           # version
            + struct.pack('BB', 7, 0)       # sequence, physical
            + struct.pack('<H', 3)          # universe (LE)
            + struct.pack('>H', 512)        # length (BE)
            + dmx_data
        )

        result = ArtNetDMX.unpack_dmx(payload)
        self.assertIsNotNone(result)
        self.assertEqual(result['version'], 14)
        self.assertEqual(result['sequence'], 7)
        self.assertEqual(result['physical'], 0)
        self.assertEqual(result['universe'], 3)
        self.assertEqual(result['length'], 512)
        self.assertEqual(result['dmx_data'], dmx_data)

    def test_dmx_unpack_too_short(self):
        """Unpack returns None for payload < 8 bytes"""
        self.assertIsNone(ArtNetDMX.unpack_dmx(b"\x00" * 7))
        self.assertIsNone(ArtNetDMX.unpack_dmx(b""))

    def test_dmx_unpack_truncated_data(self):
        """Unpack handles truncated DMX data gracefully"""
        payload = (
            struct.pack('>H', 14)
            + struct.pack('BB', 0, 0)
            + struct.pack('<H', 0)
            + struct.pack('>H', 512)  # Claims 512 bytes
            + b"\xFF" * 100           # Only 100 bytes available
        )
        result = ArtNetDMX.unpack_dmx(payload)
        self.assertIsNotNone(result)
        self.assertEqual(len(result['dmx_data']), 100)

    def test_dmx_roundtrip(self):
        """DMX packet survives pack → full unpack cycle"""
        original_data = bytes(i % 256 for i in range(512))
        dmx = ArtNetDMX(universe=5, sequence=100, dmx_data=original_data)
        raw = dmx.pack()

        # Unpack the full packet first
        parsed = ArtNetPacket.unpack(raw)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed['opcode'], 0x5000)

        # Then unpack the DMX payload
        result = ArtNetDMX.unpack_dmx(parsed['payload'])
        self.assertIsNotNone(result)
        self.assertEqual(result['universe'], 5)
        self.assertEqual(result['sequence'], 100)
        self.assertEqual(result['dmx_data'], original_data)

    def test_dmx_different_universes(self):
        """Different universes produce different packets"""
        dmx1 = ArtNetDMX(universe=0, dmx_data=bytes(512))
        dmx2 = ArtNetDMX(universe=1, dmx_data=bytes(512))

        # Extract universe from packed data
        raw1 = dmx1.pack()
        raw2 = dmx2.pack()
        # Offset: header(8) + opcode(2) + version(2) + seq(1) + phys(1) = 14
        uni1 = struct.unpack('<H', raw1[14:16])[0]
        uni2 = struct.unpack('<H', raw2[14:16])[0]
        self.assertEqual(uni1, 0)
        self.assertEqual(uni2, 1)


class TestArtNetControllerInit(unittest.TestCase):
    """Controller initialization tests (no network required)"""

    def test_constants_are_reasonable(self):
        """Constants have expected values"""
        self.assertEqual(ARTNET_PORT, 6454)
        self.assertEqual(RECV_BUFFER_SIZE, 4096)
        self.assertEqual(NODE_TIMEOUT_SEC, 300.0)

    def test_controller_default_init(self):
        """Controller initializes with correct defaults"""
        ctrl = ArtNetController()
        self.assertEqual(ctrl.bind_ip, "0.0.0.0")
        self.assertEqual(ctrl.port, 6454)
        self.assertFalse(ctrl.running)
        self.assertFalse(ctrl.output_paused)
        self.assertFalse(ctrl.receiving_paused)
        self.assertFalse(ctrl.auto_forward_enabled)

    def test_controller_custom_init(self):
        """Controller accepts custom bind_ip and port"""
        ctrl = ArtNetController(bind_ip="192.168.1.100", port=7000)
        self.assertEqual(ctrl.bind_ip, "192.168.1.100")
        self.assertEqual(ctrl.port, 7000)

    def test_send_dmx_without_start(self):
        """send_dmx returns False when controller not started"""
        ctrl = ArtNetController()
        result = ctrl.send_dmx(0, bytes(512))
        self.assertFalse(result)

    def test_send_dmx_with_mapping_without_start(self):
        """send_dmx_with_mapping returns False when not started"""
        ctrl = ArtNetController()
        result = ctrl.send_dmx_with_mapping(0, bytes(512))
        self.assertFalse(result)

    def test_pause_resume_output(self):
        """Output pause/resume toggles correctly"""
        ctrl = ArtNetController()
        self.assertFalse(ctrl.output_paused)
        ctrl.pause_output()
        self.assertTrue(ctrl.output_paused)
        ctrl.resume_output()
        self.assertFalse(ctrl.output_paused)

    def test_pause_resume_receiving(self):
        """DMX receiving pause/resume toggles correctly"""
        ctrl = ArtNetController()
        self.assertFalse(ctrl.receiving_paused)
        ctrl.pause_dmx_receiving()
        self.assertTrue(ctrl.receiving_paused)
        ctrl.resume_dmx_receiving()
        self.assertFalse(ctrl.receiving_paused)

    def test_auto_forward_requires_mapping(self):
        """Cannot enable auto-forward without mapping"""
        ctrl = ArtNetController()
        self.assertFalse(ctrl.set_auto_forward(True))
        self.assertFalse(ctrl.is_auto_forward_enabled())

    def test_auto_forward_with_mapping(self):
        """Can enable auto-forward when mapping is set"""
        ctrl = ArtNetController()
        ctrl.set_universe_mapping({"192.168.1.100": {0: 0}})
        self.assertTrue(ctrl.set_auto_forward(True))
        self.assertTrue(ctrl.is_auto_forward_enabled())

    def test_set_universe_mapping(self):
        """Universe mapping is stored correctly"""
        ctrl = ArtNetController()
        mapping = {
            "192.168.1.100": {0: 0, 1: 1},
            "192.168.1.101": {0: 2},
        }
        ctrl.set_universe_mapping(mapping)
        # Should be a copy, not reference
        mapping["192.168.1.102"] = {0: 3}
        self.assertNotIn("192.168.1.102", ctrl.universe_mapping)

    def test_empty_mapping_disables_auto_forward(self):
        """Setting empty mapping disables auto-forward"""
        ctrl = ArtNetController()
        ctrl.set_universe_mapping({"192.168.1.100": {0: 0}})
        ctrl.set_auto_forward(True)
        self.assertTrue(ctrl.is_auto_forward_enabled())

        ctrl.set_universe_mapping({})
        self.assertFalse(ctrl.is_auto_forward_enabled())

    def test_get_universe_data_default(self):
        """get_universe_data returns None for unknown universe"""
        ctrl = ArtNetController()
        self.assertIsNone(ctrl.get_universe_data(0))

    def test_get_discovered_nodes_default(self):
        """get_discovered_nodes returns empty list initially"""
        ctrl = ArtNetController()
        self.assertEqual(ctrl.get_discovered_nodes(), [])

    def test_poll_network_without_start(self):
        """poll_network does nothing when not started"""
        ctrl = ArtNetController()
        # Should not raise exception
        ctrl.poll_network()

    def test_timecode_callbacks(self):
        """Timecode callback register/unregister"""
        ctrl = ArtNetController()
        cb = lambda data, addr: None
        ctrl.register_timecode_callback(cb)
        self.assertEqual(len(ctrl.timecode_callbacks), 1)

        ctrl.unregister_timecode_callback(cb)
        self.assertEqual(len(ctrl.timecode_callbacks), 0)

    def test_timecode_no_duplicate_callback(self):
        """Registering same callback twice doesn't duplicate"""
        ctrl = ArtNetController()
        cb = lambda data, addr: None
        ctrl.register_timecode_callback(cb)
        ctrl.register_timecode_callback(cb)
        self.assertEqual(len(ctrl.timecode_callbacks), 1)


if __name__ == '__main__':
    unittest.main()