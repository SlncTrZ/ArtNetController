"""
Timeline Editor Widget - Advanced timeline editing for DMX recordings and music
Similar to video editing software timeline with zoom, trim, cut, and drag operations

Topic: gui
Last Updated: 2026-05-01
"""

import logging
from typing import Optional, List, Tuple
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QSlider, QSpinBox, QGroupBox,
                              QScrollArea, QToolBar, QMenu, QFileDialog)
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal, QTimer
from PyQt6.QtGui import (QPainter, QColor, QPen, QBrush, QPainterPath, 
                         QMouseEvent, QWheelEvent, QCursor, QFont)

logger = logging.getLogger(__name__)


class TimelineClip:
    """Represents a clip on the timeline (DMX recording or audio)"""
    
    def __init__(self, start_time: float, duration: float, clip_type: str, name: str = ""):
        self.start_time = start_time  # Start time in seconds
        self.duration = duration      # Duration in seconds
        self.clip_type = clip_type    # "dmx" or "audio"
        self.name = name
        self.selected = False
        self.trimming = None          # None, "start", "end" when trimming
        
        # For cut/split operations
        self.cuts = []  # List of cut points within the clip
        
    @property
    def end_time(self):
        """End time of clip"""
        return self.start_time + self.duration
    
    def contains_point(self, time: float) -> bool:
        """Check if time point is within clip"""
        return self.start_time <= time <= self.end_time
    
    def get_rect(self, x: float, y: float, width: float, height: float) -> QRectF:
        """Get rendering rectangle for this clip"""
        return QRectF(x, y, width, height)


class TimelineTrack(QWidget):
    """Individual timeline track (DMX or Audio)"""
    
    clip_selected = pyqtSignal(object)  # Emits selected clip
    clip_moved = pyqtSignal(object, float)  # Emits clip and new start_time
    clip_trimmed = pyqtSignal(object, float, float)  # Emits clip, new start, new duration
    playhead_moved = pyqtSignal(float)  # Emits new playhead time
    
    def __init__(self, track_type: str, track_name: str, color: QColor):
        super().__init__()
        self.track_type = track_type  # "dmx" or "audio"
        self.track_name = track_name
        self.track_color = color
        self.clips: List[TimelineClip] = []
        
        # View settings
        self.zoom_level = 1.0  # Pixels per second
        self.scroll_offset = 0  # Horizontal scroll in seconds
        
        # Playhead
        self.playhead_time = 0.0  # Current playhead position in seconds
        self.dragging_playhead = False
        
        # Interaction state
        self.dragging_clip = None
        self.drag_start_pos = None
        self.drag_start_time = None
        self.trim_handle_size = 8  # Pixels for trim handle
        
        self.setMinimumHeight(80)
        self.setMouseTracking(True)  # Enable hover effects
        
    def set_zoom(self, zoom: float):
        """Set zoom level (pixels per second)"""
        self.zoom_level = max(0.1, min(zoom, 100.0))
        self.update()
        
    def set_scroll(self, offset: float):
        """Set scroll offset in seconds"""
        self.scroll_offset = max(0, offset)
        self.update()
        
    def add_clip(self, clip: TimelineClip):
        """Add clip to track"""
        self.clips.append(clip)
        self.update()
        
    def remove_clip(self, clip: TimelineClip):
        """Remove clip from track"""
        if clip in self.clips:
            self.clips.remove(clip)
            self.update()
            
    def time_to_x(self, time: float) -> float:
        """Convert time to X coordinate"""
        return (time - self.scroll_offset) * self.zoom_level
    
    def x_to_time(self, x: float) -> float:
        """Convert X coordinate to time"""
        return (x / self.zoom_level) + self.scroll_offset
    
    def get_clip_at_pos(self, x: float) -> Optional[TimelineClip]:
        """Get clip at X position"""
        time = self.x_to_time(x)
        for clip in self.clips:
            if clip.contains_point(time):
                return clip
        return None
    
    def get_trim_handle(self, clip: TimelineClip, x: float) -> Optional[str]:
        """Check if mouse is over trim handle. Returns 'start' or 'end' or None"""
        clip_start_x = self.time_to_x(clip.start_time)
        clip_end_x = self.time_to_x(clip.end_time)
        
        if abs(x - clip_start_x) < self.trim_handle_size:
            return "start"
        elif abs(x - clip_end_x) < self.trim_handle_size:
            return "end"
        return None
    
    def paintEvent(self, event):
        """Paint the timeline track"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), QColor("#2b2b2b"))
        
        # Draw track header background
        header_height = 25
        painter.fillRect(0, 0, self.width(), header_height, QColor("#1e1e1e"))
        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        painter.drawText(10, 18, self.track_name)
        
        # Draw time ruler (adaptive interval based on zoom)
        visible_start = self.scroll_offset
        visible_end = self.scroll_offset + (self.width() / max(self.zoom_level, 0.01))
        visible_duration = visible_end - visible_start
        
        # Choose ruler interval based on visible duration
        if visible_duration > 600:
            ruler_interval = 60  # Every minute
            label_interval = 60
        elif visible_duration > 120:
            ruler_interval = 10
            label_interval = 30
        elif visible_duration > 30:
            ruler_interval = 5
            label_interval = 10
        else:
            ruler_interval = 1
            label_interval = 5
        
        painter.setPen(QPen(QColor("#555555"), 1))
        t = int(visible_start / ruler_interval) * ruler_interval
        while t <= visible_end + ruler_interval:
            x = self.time_to_x(t)
            if 0 <= x <= self.width():
                painter.drawLine(int(x), header_height, int(x), self.height())
                if t % label_interval == 0:
                    painter.setPen(QColor("#888888"))
                    if t >= 60:
                        mins = int(t) // 60
                        secs = int(t) % 60
                        label = f"{mins}:{secs:02d}"
                    else:
                        label = f"{t:.0f}s"
                    painter.drawText(int(x) + 2, header_height + 15, label)
                    painter.setPen(QPen(QColor("#555555"), 1))
            t += ruler_interval
        
        # Draw clips
        clip_y = header_height + 5
        clip_height = self.height() - header_height - 10
        
        for clip in self.clips:
            clip_start_x = self.time_to_x(clip.start_time)
            clip_width = clip.duration * self.zoom_level
            
            # Skip clips outside visible area
            if clip_start_x + clip_width < 0 or clip_start_x > self.width():
                continue
            
            # Clip rect
            clip_rect = QRectF(clip_start_x, clip_y, clip_width, clip_height)
            
            # Draw clip background
            clip_color = self.track_color if not clip.selected else QColor("#4caf50")
            painter.fillRect(clip_rect, clip_color)
            
            # Draw clip border
            border_color = QColor("#ffffff") if clip.selected else QColor("#444444")
            painter.setPen(QPen(border_color, 2 if clip.selected else 1))
            painter.drawRect(clip_rect)
            
            # Draw clip name
            painter.setPen(QColor("#ffffff"))
            painter.setFont(QFont("Arial", 8))
            clip_name = clip.name or f"{clip.clip_type.upper()} Clip"
            painter.drawText(clip_rect.adjusted(5, 5, -5, -5), 
                           Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                           clip_name)
            
            # Draw duration
            duration_text = f"{clip.duration:.2f}s"
            painter.drawText(clip_rect.adjusted(5, 0, -5, -5),
                           Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom,
                           duration_text)
            
            # Draw trim handles
            if clip.selected:
                handle_color = QColor("#ffeb3b")
                left_handle_rect = QRectF(clip_start_x, clip_y, self.trim_handle_size, clip_height)
                right_handle_rect = QRectF(
                    clip_start_x + clip_width - self.trim_handle_size,
                    clip_y,
                    self.trim_handle_size,
                    clip_height,
                )
                painter.fillRect(left_handle_rect, handle_color)
                painter.fillRect(right_handle_rect, handle_color)
        
        # Draw playhead (red vertical line with triangle head)
        playhead_x = self.time_to_x(self.playhead_time)
        if 0 <= playhead_x <= self.width():
            # Playhead line
            painter.setPen(QPen(QColor("#ff4444"), 2))
            painter.drawLine(int(playhead_x), 0, int(playhead_x), self.height())
            
            # Playhead triangle at top
            triangle = QPainterPath()
            triangle.moveTo(playhead_x - 6, 0)
            triangle.lineTo(playhead_x + 6, 0)
            triangle.lineTo(playhead_x, 10)
            triangle.closeSubpath()
            painter.fillPath(triangle, QColor("#ff4444"))
            
            # Time label at playhead
            painter.setPen(QColor("#ff4444"))
            painter.setFont(QFont("Arial", 7, QFont.Weight.Bold))
            ph_time = self.playhead_time
            if ph_time >= 60:
                ph_label = f"{int(ph_time)//60}:{int(ph_time)%60:02d}.{int(ph_time*10)%10}"
            else:
                ph_label = f"{ph_time:.1f}s"
            painter.drawText(int(playhead_x) + 4, self.height() - 3, ph_label)
    
    def _is_near_playhead(self, x: float) -> bool:
        """Check if x position is near the playhead"""
        playhead_x = self.time_to_x(self.playhead_time)
        return abs(x - playhead_x) < 8
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press"""
        if event.button() == Qt.MouseButton.LeftButton:
            x = event.position().x()
            
            # Check playhead first
            if self._is_near_playhead(x):
                self.dragging_playhead = True
                return
            
            clip = self.get_clip_at_pos(x)
            
            if clip:
                # Check if clicking on trim handle
                trim_handle = self.get_trim_handle(clip, x)
                if trim_handle:
                    clip.trimming = trim_handle
                    self.dragging_clip = clip
                    self.drag_start_pos = x
                    self.drag_start_time = clip.start_time if trim_handle == "start" else clip.end_time
                else:
                    # Start dragging clip
                    self.dragging_clip = clip
                    self.drag_start_pos = x
                    self.drag_start_time = clip.start_time
                
                # Select clip
                for c in self.clips:
                    c.selected = False
                clip.selected = True
                self.clip_selected.emit(clip)
                self.update()
            else:
                # Click on empty area: move playhead
                new_time = max(0, self.x_to_time(x))
                self.playhead_time = new_time
                self.playhead_moved.emit(new_time)
                self.dragging_playhead = True
                self.update()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move"""
        x = event.position().x()
        
        if self.dragging_playhead:
            new_time = max(0, self.x_to_time(x))
            self.playhead_time = new_time
            self.playhead_moved.emit(new_time)
            self.update()
            return
        
        if self.dragging_clip:
            delta_time = (x - self.drag_start_pos) / self.zoom_level
            
            if self.dragging_clip.trimming == "start":
                # Trim start
                new_start = max(0, self.drag_start_time + delta_time)
                new_duration = self.dragging_clip.end_time - new_start
                if new_duration > 0.1:  # Minimum duration
                    self.dragging_clip.start_time = new_start
                    self.dragging_clip.duration = new_duration
                    self.clip_trimmed.emit(self.dragging_clip, new_start, new_duration)
            elif self.dragging_clip.trimming == "end":
                # Trim end
                new_end = max(self.dragging_clip.start_time + 0.1, self.drag_start_time + delta_time)
                new_duration = new_end - self.dragging_clip.start_time
                self.dragging_clip.duration = new_duration
                self.clip_trimmed.emit(self.dragging_clip, self.dragging_clip.start_time, new_duration)
            else:
                # Move clip
                new_start = max(0, self.drag_start_time + delta_time)
                self.dragging_clip.start_time = new_start
                self.clip_moved.emit(self.dragging_clip, new_start)
            
            self.update()
        else:
            # Update cursor based on position
            if self._is_near_playhead(x):
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            else:
                clip = self.get_clip_at_pos(x)
                if clip:
                    trim_handle = self.get_trim_handle(clip, x)
                    if trim_handle:
                        self.setCursor(Qt.CursorShape.SizeHorCursor)
                    else:
                        self.setCursor(Qt.CursorShape.OpenHandCursor)
                else:
                    self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release"""
        if self.dragging_playhead:
            self.dragging_playhead = False
            return
        if self.dragging_clip:
            self.dragging_clip.trimming = None
            self.dragging_clip = None
            self.drag_start_pos = None
            self.drag_start_time = None
            self.setCursor(Qt.CursorShape.ArrowCursor)


class TimelineEditor(QWidget):
    """Complete timeline editor with multiple tracks"""
    
    timeline_changed = pyqtSignal()  # Emitted when timeline is modified
    audio_added = pyqtSignal(str, float)  # Emitted when audio added (file_path, duration)
    playhead_changed = pyqtSignal(float)  # Emitted when playhead moves
    
    def __init__(self):
        super().__init__()
        self.dmx_track = None
        self.audio_track = None
        self.current_zoom = 50.0  # Pixels per second
        self.scroll_offset = 0.0
        self.playhead_time = 0.0
        self._added_audio_path = None  # Store path of added audio
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)
        
        # Playhead info bar
        self.playhead_label = QLabel("Playhead: 0.00s")
        self.playhead_label.setStyleSheet("color: #ff4444; font-weight: bold; padding: 2px 5px;")
        layout.addWidget(self.playhead_label)
        
        # Timeline tracks container
        tracks_widget = QWidget()
        tracks_layout = QVBoxLayout(tracks_widget)
        tracks_layout.setContentsMargins(0, 0, 0, 0)
        tracks_layout.setSpacing(2)
        
        # DMX Track
        self.dmx_track = TimelineTrack("dmx", "DMX Recording", QColor("#2196f3"))
        self.dmx_track.clip_selected.connect(self.on_clip_selected)
        self.dmx_track.clip_moved.connect(self.on_clip_moved)
        self.dmx_track.clip_trimmed.connect(self.on_clip_trimmed)
        self.dmx_track.playhead_moved.connect(self._sync_playhead)
        tracks_layout.addWidget(self.dmx_track)
        
        # Audio Track
        self.audio_track = TimelineTrack("audio", "Music/Audio", QColor("#9c27b0"))
        self.audio_track.clip_selected.connect(self.on_clip_selected)
        self.audio_track.clip_moved.connect(self.on_clip_moved)
        self.audio_track.clip_trimmed.connect(self.on_clip_trimmed)
        self.audio_track.playhead_moved.connect(self._sync_playhead)
        tracks_layout.addWidget(self.audio_track)
        
        tracks_layout.addStretch()
        
        # Scroll area for tracks
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(tracks_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        layout.addWidget(self.scroll_area)
        
        # Sync zoom and scroll
        self.update_track_view()
        
        # Install event filter for Ctrl+scroll zoom
        self.scroll_area.installEventFilter(self)
        
    def create_toolbar(self) -> QWidget:
        """Create toolbar with editing tools"""
        toolbar_widget = QWidget()
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(5, 5, 5, 5)
        
        # Zoom controls
        toolbar_layout.addWidget(QLabel("Zoom:"))
        
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(1, 500)  # 1-500 pixels per second (wider range)
        self.zoom_slider.setValue(int(self.current_zoom))
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        self.zoom_slider.setMaximumWidth(150)
        toolbar_layout.addWidget(self.zoom_slider)
        
        self.zoom_label = QLabel(f"{self.current_zoom:.0f}px/s")
        self.zoom_label.setMinimumWidth(55)
        toolbar_layout.addWidget(self.zoom_label)
        
        toolbar_layout.addWidget(QLabel(" | "))
        
        # Fit buttons
        fit_all_btn = QPushButton("Fit All")
        fit_all_btn.setToolTip("Fit entire timeline to view")
        fit_all_btn.clicked.connect(self.fit_all)
        toolbar_layout.addWidget(fit_all_btn)
        
        fit_selected_btn = QPushButton("Fit Selected")
        fit_selected_btn.setToolTip("Fit selected clip to view")
        fit_selected_btn.clicked.connect(self.fit_selected)
        toolbar_layout.addWidget(fit_selected_btn)
        
        toolbar_layout.addWidget(QLabel(" | "))
        
        # Add Music button
        add_music_btn = QPushButton("+ Add Music")
        add_music_btn.setToolTip("Add audio/music file to timeline")
        add_music_btn.setStyleSheet("""
            QPushButton {
                background-color: #9c27b0;
                color: white;
                font-weight: bold;
                padding: 4px 12px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #7b1fa2; }
        """)
        add_music_btn.clicked.connect(self._add_music_from_file)
        toolbar_layout.addWidget(add_music_btn)
        
        toolbar_layout.addWidget(QLabel(" | "))
        
        # Edit tools
        cut_btn = QPushButton("Cut at Playhead")
        cut_btn.setToolTip("Cut selected clip at playhead position")
        cut_btn.clicked.connect(self.cut_selected_clip)
        toolbar_layout.addWidget(cut_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.setToolTip("Delete selected clip")
        delete_btn.clicked.connect(self.delete_selected_clip)
        toolbar_layout.addWidget(delete_btn)
        
        toolbar_layout.addStretch()
        
        # Hint label
        hint = QLabel("Ctrl+Scroll to zoom | Click timeline to move playhead")
        hint.setStyleSheet("color: #888888; font-size: 10px;")
        toolbar_layout.addWidget(hint)
        
        return toolbar_widget
    
    def eventFilter(self, obj, event):
        """Event filter for Ctrl+scroll zoom on scroll area"""
        if event.type() == event.Type.Wheel and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Ctrl+Scroll = zoom
            delta = event.angleDelta().y()
            # Calculate zoom centered on mouse position
            mouse_x = event.position().x()
            time_at_mouse = (mouse_x / max(self.current_zoom, 0.01)) + self.scroll_offset
            
            zoom_factor = 1.15 if delta > 0 else (1 / 1.15)
            new_zoom = max(1, min(500, self.current_zoom * zoom_factor))
            
            # Adjust scroll offset to keep mouse position stable
            self.current_zoom = new_zoom
            self.scroll_offset = max(0, time_at_mouse - (mouse_x / max(new_zoom, 0.01)))
            
            self.zoom_slider.blockSignals(True)
            self.zoom_slider.setValue(int(new_zoom))
            self.zoom_slider.blockSignals(False)
            self.zoom_label.setText(f"{new_zoom:.0f}px/s")
            self.update_track_view()
            return True  # Consume the event
        return super().eventFilter(obj, event)
    
    def wheelEvent(self, event: QWheelEvent):
        """Handle wheel events on the editor itself"""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            mouse_x = event.position().x()
            time_at_mouse = (mouse_x / max(self.current_zoom, 0.01)) + self.scroll_offset
            
            zoom_factor = 1.15 if delta > 0 else (1 / 1.15)
            new_zoom = max(1, min(500, self.current_zoom * zoom_factor))
            
            self.current_zoom = new_zoom
            self.scroll_offset = max(0, time_at_mouse - (mouse_x / max(new_zoom, 0.01)))
            
            self.zoom_slider.blockSignals(True)
            self.zoom_slider.setValue(int(new_zoom))
            self.zoom_slider.blockSignals(False)
            self.zoom_label.setText(f"{new_zoom:.0f}px/s")
            self.update_track_view()
            event.accept()
        else:
            # Regular scroll = pan timeline horizontally
            delta = event.angleDelta().y()
            pan_amount = 30 / max(self.current_zoom, 0.01)  # Pan ~30px worth
            if delta > 0:
                self.scroll_offset = max(0, self.scroll_offset - pan_amount)
            else:
                self.scroll_offset += pan_amount
            self.update_track_view()
            event.accept()
    
    def _sync_playhead(self, time: float):
        """Sync playhead across all tracks"""
        self.playhead_time = time
        if self.dmx_track:
            self.dmx_track.playhead_time = time
            self.dmx_track.update()
        if self.audio_track:
            self.audio_track.playhead_time = time
            self.audio_track.update()
        # Update label
        if time >= 60:
            mins = int(time) // 60
            secs = int(time) % 60
            ms = int(time * 100) % 100
            self.playhead_label.setText(f"Playhead: {mins}:{secs:02d}.{ms:02d}")
        else:
            self.playhead_label.setText(f"Playhead: {time:.2f}s")
        self.playhead_changed.emit(time)
    
    def _add_music_from_file(self):
        """Open file dialog to add music/audio to the audio track"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Add Music / Audio",
            "",
            "Audio Files (*.mp3 *.wav *.ogg *.flac *.m4a *.aac);;All Files (*)"
        )
        if not file_path:
            return
        
        # Try to get audio duration
        audio_duration = 0
        try:
            import mutagen
            audio_info = mutagen.File(file_path)
            if audio_info and audio_info.info:
                audio_duration = audio_info.info.length
        except Exception:
            pass
        
        if audio_duration <= 0:
            # Fallback: estimate from file size (rough: ~128kbps for mp3)
            try:
                import os
                file_size = os.path.getsize(file_path)
                audio_duration = file_size / (128 * 1024 / 8)  # ~128kbps estimate
            except Exception:
                audio_duration = 60  # Default 60s
        
        # Get filename for display
        from pathlib import Path
        audio_name = Path(file_path).name
        
        # Set audio clip on the audio track
        self.set_audio_clip(0, audio_duration, audio_name)
        self._added_audio_path = file_path
        
        self.audio_added.emit(file_path, audio_duration)
        self.timeline_changed.emit()
        
        logger.info(f"Added audio: {audio_name} ({audio_duration:.1f}s)")
    
    def get_added_audio_path(self) -> Optional[str]:
        """Get the file path of audio added via the Add Music button"""
        return self._added_audio_path
    
    def on_zoom_changed(self, value: int):
        """Handle zoom change"""
        self.current_zoom = float(value)
        self.zoom_label.setText(f"{self.current_zoom:.0f}px/s")
        self.update_track_view()
        
    def update_track_view(self):
        """Update zoom and scroll for all tracks"""
        if self.dmx_track:
            self.dmx_track.set_zoom(self.current_zoom)
            self.dmx_track.set_scroll(self.scroll_offset)
        if self.audio_track:
            self.audio_track.set_zoom(self.current_zoom)
            self.audio_track.set_scroll(self.scroll_offset)
    
    def fit_all(self):
        """Fit all clips in view"""
        max_duration = 0
        for track in [self.dmx_track, self.audio_track]:
            if track:
                for clip in track.clips:
                    max_duration = max(max_duration, clip.end_time)
        
        if max_duration > 0:
            available_width = self.width() if self.width() > 100 else 800
            self.current_zoom = available_width / max_duration * 0.9
            self.current_zoom = max(1, min(500, self.current_zoom))
            self.zoom_slider.setValue(int(self.current_zoom))
            self.scroll_offset = 0
            self.update_track_view()
    
    def fit_selected(self):
        """Fit selected clip in view"""
        for track in [self.dmx_track, self.audio_track]:
            if track:
                for clip in track.clips:
                    if clip.selected:
                        available_width = self.width() if self.width() > 100 else 800
                        self.current_zoom = available_width / clip.duration * 0.9
                        self.current_zoom = max(1, min(500, self.current_zoom))
                        self.zoom_slider.setValue(int(self.current_zoom))
                        self.scroll_offset = clip.start_time
                        self.update_track_view()
                        return
    
    def on_clip_selected(self, clip: TimelineClip):
        """Handle clip selection"""
        logger.info(f"Clip selected: {clip.name} ({clip.clip_type})")
        
    def on_clip_moved(self, clip: TimelineClip, new_start: float):
        """Handle clip moved"""
        logger.info(f"Clip moved to {new_start:.2f}s")
        self.timeline_changed.emit()
        
    def on_clip_trimmed(self, clip: TimelineClip, new_start: float, new_duration: float):
        """Handle clip trimmed"""
        logger.info(f"Clip trimmed: start={new_start:.2f}s, duration={new_duration:.2f}s")
        self.timeline_changed.emit()
    
    def cut_selected_clip(self):
        """Cut selected clip at playhead position"""
        for track in [self.dmx_track, self.audio_track]:
            if track:
                for clip in track.clips:
                    if clip.selected and clip.contains_point(self.playhead_time):
                        cut_time = self.playhead_time
                        # Create second half
                        second_duration = clip.end_time - cut_time
                        if second_duration < 0.1 or (cut_time - clip.start_time) < 0.1:
                            return  # Too close to edge
                        
                        second_clip = TimelineClip(
                            cut_time, second_duration, clip.clip_type,
                            f"{clip.name} (cut)"
                        )
                        # Trim original to first half
                        clip.duration = cut_time - clip.start_time
                        clip.selected = False
                        second_clip.selected = True
                        track.add_clip(second_clip)
                        
                        logger.info(f"Cut clip at {cut_time:.2f}s")
                        self.timeline_changed.emit()
                        return
        
    def delete_selected_clip(self):
        """Delete selected clip"""
        for track in [self.dmx_track, self.audio_track]:
            if track:
                for clip in track.clips[:]:
                    if clip.selected:
                        track.remove_clip(clip)
                        logger.info(f"Deleted clip: {clip.name}")
                        self.timeline_changed.emit()
                        return
    
    def set_dmx_clip(self, duration: float, name: str = "DMX Recording"):
        """Set DMX recording clip"""
        if self.dmx_track:
            self.dmx_track.clips.clear()
            clip = TimelineClip(0, duration, "dmx", name)
            self.dmx_track.add_clip(clip)
            
    def set_audio_clip(self, start_time: float, duration: float, name: str = "Audio"):
        """Set audio clip"""
        if self.audio_track:
            self.audio_track.clips.clear()
            clip = TimelineClip(start_time, duration, "audio", name)
            self.audio_track.add_clip(clip)
    
    def get_dmx_clip(self) -> Optional[TimelineClip]:
        """Get DMX clip"""
        if self.dmx_track and self.dmx_track.clips:
            return self.dmx_track.clips[0]
        return None
    
    def get_audio_clip(self) -> Optional[TimelineClip]:
        """Get audio clip"""
        if self.audio_track and self.audio_track.clips:
            return self.audio_track.clips[0]
        return None
