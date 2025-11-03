"""
Test Art-Net Controller functionality
"""

import sys
import unittest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from artnet.controller import ArtNetController, ArtNetPacket
from show.manager import ShowManager, Show, ShowMetadata, PlaylistItem, DMXScene
from utils.config import ConfigManager

class TestArtNetController(unittest.TestCase):
    """Test Art-Net controller"""
    
    def setUp(self):
        self.controller = ArtNetController(bind_ip="127.0.0.1")
    
    def test_packet_creation(self):
        """Test packet creation"""
        from artnet.controller import ArtNetDMX
        
        dmx_data = bytes([255, 128, 64] + [0] * 509)
        packet = ArtNetDMX(universe=0, sequence=1, dmx_data=dmx_data)
        
        packed = packet.pack()
        self.assertIsInstance(packed, bytes)
        self.assertTrue(len(packed) > 10)
    
    def test_packet_unpacking(self):
        """Test packet unpacking"""
        from artnet.controller import ArtNetDMX
        
        dmx_data = bytes([255, 128, 64] + [0] * 509)
        packet = ArtNetDMX(universe=0, sequence=1, dmx_data=dmx_data)
        packed = packet.pack()
        
        unpacked = ArtNetPacket.unpack(packed)
        self.assertIsNotNone(unpacked)
        self.assertEqual(unpacked['opcode'], ArtNetPacket.ARTNET_DMX)

class TestShowManager(unittest.TestCase):
    """Test show manager"""
    
    def setUp(self):
        self.test_dir = Path("test_shows")
        self.test_dir.mkdir(exist_ok=True)
        self.manager = ShowManager(str(self.test_dir))
    
    def tearDown(self):
        # Clean up test files
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_create_show(self):
        """Test show creation"""
        show = self.manager.create_new_show("Test Show", "A test show", "Test Author")
        
        self.assertIsInstance(show, Show)
        self.assertEqual(show.metadata.name, "Test Show")
        self.assertEqual(show.metadata.description, "A test show")
        self.assertEqual(show.metadata.author, "Test Author")
    
    def test_save_load_json(self):
        """Test JSON save/load"""
        # Create test show
        show = self.manager.create_new_show("Test JSON Show")
        
        # Add playlist item
        playlist_item = PlaylistItem(
            file_path="test.mp3",
            title="Test Song",
            artist="Test Artist",
            duration=180.0
        )
        show.playlist.append(playlist_item)
        
        # Add DMX scene
        dmx_scene = DMXScene(
            name="Test Scene",
            universe=0,
            channels={1: 255, 2: 128, 3: 64},
            timestamp=0.0
        )
        show.scenes.append(dmx_scene)
        
        # Save show
        file_path = self.test_dir / "test_show.json"
        success = self.manager.save_show(show, str(file_path), "json")
        self.assertTrue(success)
        self.assertTrue(file_path.exists())
        
        # Load show
        loaded_show = self.manager.load_show(str(file_path))
        self.assertIsNotNone(loaded_show)
        self.assertEqual(loaded_show.metadata.name, "Test JSON Show")
        self.assertEqual(len(loaded_show.playlist), 1)
        self.assertEqual(len(loaded_show.scenes), 1)
        self.assertEqual(loaded_show.playlist[0].title, "Test Song")
        self.assertEqual(loaded_show.scenes[0].name, "Test Scene")
    
    def test_save_load_xml(self):
        """Test XML save/load"""
        # Create test show
        show = self.manager.create_new_show("Test XML Show")
        
        # Add playlist item
        playlist_item = PlaylistItem(
            file_path="test.mp3",
            title="Test Song XML",
            artist="Test Artist XML",
            duration=200.0
        )
        show.playlist.append(playlist_item)
        
        # Save show
        file_path = self.test_dir / "test_show.xml"
        success = self.manager.save_show(show, str(file_path), "xml")
        self.assertTrue(success)
        self.assertTrue(file_path.exists())
        
        # Load show
        loaded_show = self.manager.load_show(str(file_path))
        self.assertIsNotNone(loaded_show)
        self.assertEqual(loaded_show.metadata.name, "Test XML Show")
        self.assertEqual(len(loaded_show.playlist), 1)
        self.assertEqual(loaded_show.playlist[0].title, "Test Song XML")

class TestConfigManager(unittest.TestCase):
    """Test config manager"""
    
    def setUp(self):
        self.test_config_dir = Path("test_config")
        self.test_config_dir.mkdir(exist_ok=True)
        self.manager = ConfigManager(str(self.test_config_dir))
    
    def tearDown(self):
        # Clean up test files
        import shutil
        if self.test_config_dir.exists():
            shutil.rmtree(self.test_config_dir)
    
    def test_config_operations(self):
        """Test config get/set operations"""
        # Set config
        self.manager.set_app_config('test.value', 123)
        self.manager.set_app_config('test.nested.value', 'hello')
        
        # Get config
        self.assertEqual(self.manager.get_app_config('test.value'), 123)
        self.assertEqual(self.manager.get_app_config('test.nested.value'), 'hello')
        self.assertEqual(self.manager.get_app_config('nonexistent', 'default'), 'default')
        
        # Save and reload
        self.manager.save_configs()
        
        new_manager = ConfigManager(str(self.test_config_dir))
        self.assertEqual(new_manager.get_app_config('test.value'), 123)
        self.assertEqual(new_manager.get_app_config('test.nested.value'), 'hello')

if __name__ == '__main__':
    unittest.main()