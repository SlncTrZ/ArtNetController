"""
Show Management System
Quản lý show với XML/JSON format và playlist nhạc
"""

import json
import xml.etree.ElementTree as ET
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import shutil

logger = logging.getLogger(__name__)

@dataclass
class PlaylistItem:
    """Item trong playlist"""
    file_path: str
    title: str
    artist: str = ""
    duration: float = 0.0
    start_time: float = 0.0  # Thời gian bắt đầu trong show
    fade_in: float = 0.0
    fade_out: float = 0.0
    loop: bool = False

@dataclass
class DMXScene:
    """DMX scene trong show"""
    name: str
    universe: int
    channels: Dict[int, int]  # channel -> value
    timestamp: float = 0.0
    duration: float = 0.0
    fade_time: float = 0.0

@dataclass
class ShowMetadata:
    """Metadata của show"""
    name: str
    description: str = ""
    author: str = ""
    created_date: str = ""
    modified_date: str = ""
    version: str = "1.0"
    duration: float = 0.0
    bpm: float = 120.0
    universes: List[int] = None
    
    def __post_init__(self):
        if self.universes is None:
            self.universes = []
        if not self.created_date:
            self.created_date = datetime.now().isoformat()

@dataclass
class Show:
    """Show data structure"""
    metadata: ShowMetadata
    playlist: List[PlaylistItem]
    scenes: List[DMXScene]
    
    def __post_init__(self):
        if not self.playlist:
            self.playlist = []
        if not self.scenes:
            self.scenes = []

class ShowManager:
    """Quản lý shows"""
    
    def __init__(self, shows_path: str = "data/shows"):
        self.shows_path = Path(shows_path)
        self.shows_path.mkdir(parents=True, exist_ok=True)
        
        self.current_show: Optional[Show] = None
        self.current_show_path: Optional[Path] = None
    
    def create_new_show(self, name: str, description: str = "", author: str = "") -> Show:
        """Tạo show mới"""
        metadata = ShowMetadata(
            name=name,
            description=description,
            author=author,
            created_date=datetime.now().isoformat()
        )
        
        show = Show(
            metadata=metadata,
            playlist=[],
            scenes=[]
        )
        
        self.current_show = show
        logger.info(f"Created new show: {name}")
        return show
    
    def save_show(self, show: Show, file_path: str = None, format: str = "json") -> bool:
        """Lưu show"""
        try:
            if file_path is None:
                if self.current_show_path:
                    file_path = self.current_show_path
                else:
                    # Generate filename from show name
                    safe_name = "".join(c for c in show.metadata.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    file_path = self.shows_path / f"{safe_name}.{format}"
            else:
                file_path = Path(file_path)
            
            # Update modified date
            show.metadata.modified_date = datetime.now().isoformat()
            
            if format.lower() == "json":
                self._save_json(show, file_path)
            elif format.lower() == "xml":
                self._save_xml(show, file_path)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            self.current_show = show
            self.current_show_path = file_path
            
            logger.info(f"Show saved: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save show: {e}")
            return False
    
    def load_show(self, file_path: str) -> Optional[Show]:
        """Load show từ file"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                logger.error(f"Show file not found: {file_path}")
                return None
            
            if file_path.suffix.lower() == ".json":
                show = self._load_json(file_path)
            elif file_path.suffix.lower() == ".xml":
                show = self._load_xml(file_path)
            else:
                logger.error(f"Unsupported file format: {file_path.suffix}")
                return None
            
            self.current_show = show
            self.current_show_path = file_path
            
            logger.info(f"Show loaded: {file_path}")
            return show
            
        except Exception as e:
            logger.error(f"Failed to load show: {e}")
            return None
    
    def _save_json(self, show: Show, file_path: Path):
        """Save show as JSON"""
        show_data = {
            'metadata': asdict(show.metadata),
            'playlist': [asdict(item) for item in show.playlist],
            'scenes': [asdict(scene) for scene in show.scenes]
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(show_data, f, indent=2, ensure_ascii=False)
    
    def _save_xml(self, show: Show, file_path: Path):
        """Save show as XML"""
        root = ET.Element("show")
        
        # Metadata
        metadata_elem = ET.SubElement(root, "metadata")
        for key, value in asdict(show.metadata).items():
            elem = ET.SubElement(metadata_elem, key)
            if isinstance(value, list):
                elem.text = ",".join(map(str, value))
            else:
                elem.text = str(value)
        
        # Playlist
        playlist_elem = ET.SubElement(root, "playlist")
        for item in show.playlist:
            item_elem = ET.SubElement(playlist_elem, "item")
            for key, value in asdict(item).items():
                elem = ET.SubElement(item_elem, key)
                elem.text = str(value)
        
        # Scenes
        scenes_elem = ET.SubElement(root, "scenes")
        for scene in show.scenes:
            scene_elem = ET.SubElement(scenes_elem, "scene")
            scene_dict = asdict(scene)
            
            for key, value in scene_dict.items():
                if key == "channels":
                    channels_elem = ET.SubElement(scene_elem, "channels")
                    for channel, dmx_value in value.items():
                        channel_elem = ET.SubElement(channels_elem, "channel")
                        channel_elem.set("number", str(channel))
                        channel_elem.text = str(dmx_value)
                else:
                    elem = ET.SubElement(scene_elem, key)
                    elem.text = str(value)
        
        # Write XML
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)
        tree.write(file_path, encoding='utf-8', xml_declaration=True)
    
    def _load_json(self, file_path: Path) -> Show:
        """Load show from JSON"""
        with open(file_path, 'r', encoding='utf-8') as f:
            show_data = json.load(f)
        
        # Parse metadata
        metadata = ShowMetadata(**show_data['metadata'])
        
        # Parse playlist
        playlist = [PlaylistItem(**item) for item in show_data.get('playlist', [])]
        
        # Parse scenes
        scenes = [DMXScene(**scene) for scene in show_data.get('scenes', [])]
        
        return Show(metadata=metadata, playlist=playlist, scenes=scenes)
    
    def _load_xml(self, file_path: Path) -> Show:
        """Load show from XML"""
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Parse metadata
        metadata_elem = root.find('metadata')
        metadata_dict = {}
        for elem in metadata_elem:
            value = elem.text
            if elem.tag == 'universes':
                value = [int(x.strip()) for x in value.split(',') if x.strip()]
            elif elem.tag in ['duration', 'bpm']:
                value = float(value)
            metadata_dict[elem.tag] = value
        
        metadata = ShowMetadata(**metadata_dict)
        
        # Parse playlist
        playlist = []
        playlist_elem = root.find('playlist')
        if playlist_elem is not None:
            for item_elem in playlist_elem.findall('item'):
                item_dict = {}
                for elem in item_elem:
                    value = elem.text
                    if elem.tag in ['duration', 'start_time', 'fade_in', 'fade_out']:
                        value = float(value)
                    elif elem.tag == 'loop':
                        value = value.lower() == 'true'
                    item_dict[elem.tag] = value
                playlist.append(PlaylistItem(**item_dict))
        
        # Parse scenes
        scenes = []
        scenes_elem = root.find('scenes')
        if scenes_elem is not None:
            for scene_elem in scenes_elem.findall('scene'):
                scene_dict = {}
                for elem in scene_elem:
                    if elem.tag == 'channels':
                        channels = {}
                        for channel_elem in elem.findall('channel'):
                            channel_num = int(channel_elem.get('number'))
                            channel_value = int(channel_elem.text)
                            channels[channel_num] = channel_value
                        scene_dict['channels'] = channels
                    else:
                        value = elem.text
                        if elem.tag in ['timestamp', 'duration', 'fade_time']:
                            value = float(value)
                        elif elem.tag == 'universe':
                            value = int(value)
                        scene_dict[elem.tag] = value
                scenes.append(DMXScene(**scene_dict))
        
        return Show(metadata=metadata, playlist=playlist, scenes=scenes)
    
    def get_show_list(self) -> List[Dict[str, Any]]:
        """Lấy danh sách shows"""
        shows = []
        
        for file_path in self.shows_path.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    show_data = json.load(f)
                
                metadata = show_data.get('metadata', {})
                shows.append({
                    'file_path': str(file_path),
                    'name': metadata.get('name', file_path.stem),
                    'description': metadata.get('description', ''),
                    'author': metadata.get('author', ''),
                    'created_date': metadata.get('created_date', ''),
                    'modified_date': metadata.get('modified_date', ''),
                    'duration': metadata.get('duration', 0.0),
                    'file_size': file_path.stat().st_size
                })
                
            except Exception as e:
                logger.warning(f"Failed to read show metadata from {file_path}: {e}")
        
        for file_path in self.shows_path.glob("*.xml"):
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
                metadata_elem = root.find('metadata')
                
                if metadata_elem is not None:
                    metadata = {}
                    for elem in metadata_elem:
                        metadata[elem.tag] = elem.text
                    
                    shows.append({
                        'file_path': str(file_path),
                        'name': metadata.get('name', file_path.stem),
                        'description': metadata.get('description', ''),
                        'author': metadata.get('author', ''),
                        'created_date': metadata.get('created_date', ''),
                        'modified_date': metadata.get('modified_date', ''),
                        'duration': float(metadata.get('duration', 0.0)),
                        'file_size': file_path.stat().st_size
                    })
                    
            except Exception as e:
                logger.warning(f"Failed to read show metadata from {file_path}: {e}")
        
        # Sort by modified date (newest first)
        shows.sort(key=lambda x: x.get('modified_date', ''), reverse=True)
        return shows
    
    def delete_show(self, file_path: str) -> bool:
        """Xóa show"""
        try:
            file_path = Path(file_path)
            
            if file_path.exists():
                file_path.unlink()
                
                # Also delete associated music folder if exists
                music_folder = file_path.parent / f"{file_path.stem}_music"
                if music_folder.exists() and music_folder.is_dir():
                    shutil.rmtree(music_folder)
                
                logger.info(f"Show deleted: {file_path}")
                return True
            else:
                logger.warning(f"Show file not found: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete show: {e}")
            return False
    
    def add_playlist_item(self, item: PlaylistItem):
        """Thêm item vào playlist"""
        if self.current_show:
            self.current_show.playlist.append(item)
            # Update show duration
            max_end_time = max([item.start_time + item.duration for item in self.current_show.playlist], default=0)
            self.current_show.metadata.duration = max_end_time
    
    def remove_playlist_item(self, index: int):
        """Xóa item khỏi playlist"""
        if self.current_show and 0 <= index < len(self.current_show.playlist):
            self.current_show.playlist.pop(index)
            # Update show duration
            max_end_time = max([item.start_time + item.duration for item in self.current_show.playlist], default=0)
            self.current_show.metadata.duration = max_end_time
    
    def add_dmx_scene(self, scene: DMXScene):
        """Thêm DMX scene"""
        if self.current_show:
            self.current_show.scenes.append(scene)
            # Update universes list
            if scene.universe not in self.current_show.metadata.universes:
                self.current_show.metadata.universes.append(scene.universe)
    
    def remove_dmx_scene(self, index: int):
        """Xóa DMX scene"""
        if self.current_show and 0 <= index < len(self.current_show.scenes):
            self.current_show.scenes.pop(index)
    
    def get_show_music_folder(self, show_name: str = None) -> Path:
        """Lấy thư mục nhạc của show"""
        if show_name is None and self.current_show:
            show_name = self.current_show.metadata.name
        
        if show_name:
            safe_name = "".join(c for c in show_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            music_folder = self.shows_path / f"{safe_name}_music"
            music_folder.mkdir(exist_ok=True)
            return music_folder
        
        return self.shows_path / "music"
    
    def import_music_file(self, source_path: str, show_name: str = None) -> Optional[str]:
        """Import music file vào show folder"""
        try:
            source_path = Path(source_path)
            music_folder = self.get_show_music_folder(show_name)
            
            # Copy file to show music folder
            dest_path = music_folder / source_path.name
            shutil.copy2(source_path, dest_path)
            
            logger.info(f"Music file imported: {dest_path}")
            return str(dest_path)
            
        except Exception as e:
            logger.error(f"Failed to import music file: {e}")
            return None
    
    def export_show(self, output_path: str, include_music: bool = True) -> bool:
        """Export show và music files"""
        if not self.current_show:
            return False
        
        try:
            output_path = Path(output_path)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Export show file
            show_file = output_path / f"{self.current_show.metadata.name}.json"
            self._save_json(self.current_show, show_file)
            
            # Export music files if requested
            if include_music:
                music_folder = self.get_show_music_folder()
                output_music = output_path / "music"
                
                if music_folder.exists():
                    shutil.copytree(music_folder, output_music, dirs_exist_ok=True)
            
            logger.info(f"Show exported to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export show: {e}")
            return False