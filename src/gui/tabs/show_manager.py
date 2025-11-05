"""
Show Manager Tab - Manage and play DMX shows with playlist controls
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTableWidget, QTableWidgetItem, QPushButton,
    QGroupBox, QListWidget, QListWidgetItem, QProgressBar, QLabel,
    QMessageBox, QHeaderView, QAbstractItemView,
    QFileDialog, QInputDialog, QDateTimeEdit, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer, QDateTime
from PyQt6.QtGui import QFont
from pathlib import Path
import json
import socket
import struct
from datetime import datetime, timezone
try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None
import time
import random

# Import DMX Binary Player for binary show playback
try:
    from show.dmx_recorder import DMXPlayer
except ImportError:
    # Fallback if module not available
    print("Warning: DMXPlayer not available - binary show playback disabled")
    DMXPlayer = None


class ShowManagerTab(QWidget):
    """Show Manager with playlist and a simple playback engine"""

    # Emit universe (int) and DMX frame (bytes)
    dmx_changed = pyqtSignal(int, bytes)

    def __init__(self, config_manager=None, artnet_controller=None, is_admin: bool = False):
        super().__init__()
        self.config_manager = config_manager
        self.artnet_controller = artnet_controller
        self._is_admin = is_admin

        # Data/state
        self.shows_data: dict[str, dict] = {}
        self.current_show_index: int = -1
        self.playback_engine: SimplePlaybackEngine | None = None

        # Modes
        self.is_playing = False
        self.is_loop = False
        self.is_shuffle = False

        # UI
        self.setObjectName("ShowManagerRoot")
        self._init_ui()
        self._load_shows()
        self._init_clock()
        self._apply_saved_background()

    # ---------------- UI ----------------
    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Header: project, time, background
        layout.addLayout(self._build_header_bar())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_library_panel())
        splitter.addWidget(self._build_playlist_panel())
        splitter.setSizes([500, 400])
        layout.addWidget(splitter)

    def _build_header_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()

        # Project name display
        self.project_name = (self.config_manager.get_app_config('project.name', 'My Project')
                             if self.config_manager else 'My Project')
        self.lbl_project = QLabel(f"Project: {self.project_name}")
        self.lbl_project.setFont(QFont("Segoe UI", 17, QFont.Weight.Bold))
        bar.addWidget(self.lbl_project, stretch=1)

        # Date/Time display (timezone can be changed via menu)
        self.lbl_time = QLabel("--:--:--")
        self.lbl_time.setFont(QFont("Segoe UI", 15))
        bar.addWidget(self.lbl_time)

        # Initialize timezone settings (buttons removed, now in menu)
        self._timezones = [
            'UTC', 'Asia/Ho_Chi_Minh', 'Asia/Bangkok', 'Europe/London', 'America/New_York'
        ]
        saved_tz = (self.config_manager.get_app_config('ui.timezone', 'UTC')
                    if self.config_manager else 'UTC')
        self._tz_index = max(0, self._timezones.index(saved_tz) if saved_tz in self._timezones else 0)

        return bar

    def _build_library_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)

        title = QLabel("Shows Library")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Show", "Duration", "Scenes", "Audio"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Disable editing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in (1, 2, 3):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)

        btns = QHBoxLayout()
        self.btn_add = QPushButton("Add to Playlist")
        self.btn_add.clicked.connect(self._add_selected_to_playlist)
        btns.addWidget(self.btn_add)

        self.btn_play_single = QPushButton("Play Single")
        self.btn_play_single.clicked.connect(self._play_single)
        btns.addWidget(self.btn_play_single)

        # Admin-only actions
        self.btn_edit = QPushButton("Edit")
        self.btn_edit.clicked.connect(self._edit_show)
        self.btn_delete = QPushButton("Delete")
        self.btn_delete.clicked.connect(self._delete_show)
        btns.addWidget(self.btn_edit)
        btns.addWidget(self.btn_delete)

        # Set initial admin state
        self.btn_edit.setEnabled(self._is_admin)
        self.btn_delete.setEnabled(self._is_admin)

        layout.addLayout(btns)
        return panel

    def _build_playlist_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)

        grp = QGroupBox("Playlist")
        grp_layout = QVBoxLayout(grp)
        self.playlist = QListWidget()
        self.playlist.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        grp_layout.addWidget(self.playlist)
        layout.addWidget(grp)

        # Controls
        controls = QHBoxLayout()
        self.btn_prev = QPushButton("Prev")
        self.btn_prev.clicked.connect(self._prev)
        controls.addWidget(self.btn_prev)

        self.btn_play = QPushButton("Play")
        self.btn_play.clicked.connect(self._toggle_play)
        controls.addWidget(self.btn_play)

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.clicked.connect(self._stop)
        controls.addWidget(self.btn_stop)

        self.btn_next = QPushButton("Next")
        self.btn_next.clicked.connect(self._next)
        controls.addWidget(self.btn_next)

        self.btn_loop = QPushButton("Loop: OFF")
        self.btn_loop.setCheckable(True)
        self.btn_loop.toggled.connect(self._toggle_loop)
        controls.addWidget(self.btn_loop)

        self.btn_shuffle = QPushButton("Shuffle: OFF")
        self.btn_shuffle.setCheckable(True)
        self.btn_shuffle.toggled.connect(self._toggle_shuffle)
        controls.addWidget(self.btn_shuffle)

        layout.addLayout(controls)

        # Progress
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        # Spotify-like time display
        self.time_readout = QLabel("00:00 / 00:00")
        layout.addWidget(self.time_readout)
        self.lbl_status = QLabel("Ready")
        layout.addWidget(self.lbl_status)

        # Playlist ops
        ops = QHBoxLayout()
        self.btn_remove = QPushButton("Remove")
        self.btn_remove.clicked.connect(self._remove_selected)
        ops.addWidget(self.btn_remove)
        self.btn_clear = QPushButton("Clear")
        self.btn_clear.clicked.connect(self.playlist.clear)
        ops.addWidget(self.btn_clear)
        layout.addLayout(ops)

        # Scheduler
        sched_grp = QGroupBox("Scheduler")
        sched_layout = QVBoxLayout(sched_grp)
        row = QHBoxLayout()
        self.sched_dt = QDateTimeEdit(QDateTime.currentDateTime())
        self.sched_dt.setDisplayFormat("yyyy-MM-dd HH:mm")
        row.addWidget(self.sched_dt)
        self.btn_schedule_selected = QPushButton("Schedule Selected Shows")
        self.btn_schedule_selected.clicked.connect(self._schedule_selected)
        row.addWidget(self.btn_schedule_selected)
        sched_layout.addLayout(row)

        self.chk_scheduler_enabled = QCheckBox("Enable Scheduler")
        self.chk_scheduler_enabled.setChecked(True)
        sched_layout.addWidget(self.chk_scheduler_enabled)

        self.sched_list = QListWidget()
        sched_layout.addWidget(self.sched_list)
        
        # Scheduler management buttons
        sched_btns = QHBoxLayout()
        self.btn_remove_schedule = QPushButton("Remove Selected")
        self.btn_remove_schedule.clicked.connect(self._remove_selected_schedule)
        sched_btns.addWidget(self.btn_remove_schedule)
        
        self.btn_clear_schedule = QPushButton("Clear All")
        self.btn_clear_schedule.clicked.connect(self._clear_all_schedules)
        sched_btns.addWidget(self.btn_clear_schedule)
        sched_layout.addLayout(sched_btns)
        
        layout.addWidget(sched_grp)

        # Scheduler timer
        self._sched_timer = QTimer(self)
        self._sched_timer.timeout.connect(self._scheduler_tick)
        self._sched_timer.start(1000)

        return panel

    # ------------- Data loading -------------
    def _load_shows(self):
        shows_dir = Path("data/shows")
        shows_dir.mkdir(parents=True, exist_ok=True)
        self.shows_data.clear()
        self.table.setRowCount(0)

        for fp in shows_dir.glob("*.json"):
            try:
                with fp.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Check if this is a binary format show (V2.0)
                format_version = data.get("format_version", "1.0")
                metadata = data.get("metadata", {})
                
                if format_version == "2.0" and "binary_file" in metadata:
                    # Binary format show
                    name = metadata.get("name", fp.stem)
                    duration = float(metadata.get("duration", 0))
                    binary_file = metadata.get("binary_file", "")
                    audio_path = data.get("audio_file") or ""
                    audio = Path(audio_path).name if audio_path else "-"
                    
                    # Check if binary file exists
                    binary_path = shows_dir / binary_file
                    if not binary_path.exists():
                        print(f"Binary file not found for show {name}: {binary_path}")
                        continue
                    
                    # Mark as binary format for playback engine
                    data["is_binary_format"] = True
                    data["binary_file_path"] = str(binary_path)
                    
                    scenes_count = "Binary"  # Binary shows don't have discrete scenes
                else:
                    # Legacy format show (V1.0)
                    name = data.get("name", fp.stem)
                    scenes = data.get("scenes", [])
                    duration = float(data.get("duration", 0)) or self._estimate_total_duration(data)
                    audio_path = data.get("audio_file") or ""
                    audio = Path(audio_path).name if audio_path else "-"
                    
                    data["is_binary_format"] = False
                    scenes_count = str(len(scenes))

                self.shows_data[name] = data
                r = self.table.rowCount()
                self.table.insertRow(r)
                self.table.setItem(r, 0, QTableWidgetItem(name))
                self.table.setItem(r, 1, QTableWidgetItem(f"{duration:.1f}s"))
                self.table.setItem(r, 2, QTableWidgetItem(scenes_count))
                self.table.setItem(r, 3, QTableWidgetItem(audio))
            except Exception as e:
                print(f"Failed to load show {fp}: {e}")

    # ------------- Playlist ops -------------
    def _add_selected_to_playlist(self):
        rows = {it.row() for it in self.table.selectedItems()}
        names_in_playlist = {self.playlist.item(i).text() for i in range(self.playlist.count())}
        for r in rows:
            name = self.table.item(r, 0).text()
            if name not in names_in_playlist:
                self.playlist.addItem(name)

    def _remove_selected(self):
        row = self.playlist.currentRow()
        if row >= 0:
            self.playlist.takeItem(row)

    def _play_single(self):
        items = self.table.selectedItems()
        if not items:
            QMessageBox.warning(self, "Warning", "Please select a show to play")
            return
        name = self.table.item(items[0].row(), 0).text()
        self.playlist.clear()
        self.playlist.addItem(name)
        self.current_show_index = 0
        self._start_playback()

    # ------------- Controls -------------
    def _toggle_play(self):
        if self.is_playing:
            self._pause()
        else:
            self._start_playback()

    def _toggle_loop(self, on: bool):
        self.is_loop = on
        self.btn_loop.setText(f"Loop: {'ON' if on else 'OFF'}")

    def _toggle_shuffle(self, on: bool):
        self.is_shuffle = on
        self.btn_shuffle.setText(f"Shuffle: {'ON' if on else 'OFF'}")

    def _prev(self):
        if self.playlist.count() == 0:
            return
        if self.is_shuffle:
            self.current_show_index = random.randint(0, self.playlist.count() - 1)
        else:
            self.current_show_index = max(0, (self.current_show_index - 1))
        if self.is_playing:
            self._play_current()

    def _next(self):
        if self.playlist.count() == 0:
            return
        if self.is_shuffle:
            self.current_show_index = random.randint(0, self.playlist.count() - 1)
        else:
            self.current_show_index += 1
            if self.current_show_index >= self.playlist.count():
                if self.is_loop:
                    self.current_show_index = 0
                else:
                    self._stop()
                    return
        if self.is_playing:
            self._play_current()

    def _start_playback(self):
        if self.playlist.count() == 0:
            QMessageBox.warning(self, "Warning", "Playlist is empty")
            return
        if self.current_show_index < 0:
            self.current_show_index = 0
        self.is_playing = True
        self.btn_play.setText("Pause")
        self._play_current()

    def _pause(self):
        self.is_playing = False
        self.btn_play.setText("Play")
        if self.playback_engine:
            self.playback_engine.pause()

    def _stop(self):
        self.is_playing = False
        self.btn_play.setText("Play")
        self.progress.setValue(0)
        self.lbl_status.setText("Stopped")
        self.current_show_index = -1
        if self.playback_engine:
            self.playback_engine.stop()
            self.playback_engine = None

    def _play_current(self):
        if not (0 <= self.current_show_index < self.playlist.count()):
            return
        name = self.playlist.item(self.current_show_index).text()
        data = self.shows_data.get(name)
        if not data:
            QMessageBox.warning(self, "Error", f"Show '{name}' not found")
            return

        # Stop previous engine
        if self.playback_engine:
            self.playback_engine.stop()

        self.playlist.setCurrentRow(self.current_show_index)
        self.lbl_status.setText(f"Playing: {name}")

        # Detect show format and use appropriate engine
        is_binary = data.get("is_binary_format", False)
        
        if is_binary:
            # Binary format show (.dmxrec)
            binary_file_path = data.get("binary_file_path")
            if not binary_file_path:
                QMessageBox.warning(self, "Error", f"Binary file path not found for show '{name}'")
                return
            
            metadata = data.get("metadata", {})
            duration = float(metadata.get("duration", 0))
            self._current_total = duration
            
            print(f"Playing binary show: {name} ({binary_file_path})")
            self.playback_engine = BinaryPlaybackEngine(binary_file_path, duration)
        else:
            # Legacy format show (scenes)
            total_seconds = float(data.get("duration", 0)) or self._estimate_total_duration(data)
            self._current_total = total_seconds
            
            print(f"Playing legacy show: {name}")
            self.playback_engine = SimplePlaybackEngine(data)

        # Connect signals (same for both engines)
        self.playback_engine.progress_updated.connect(self._on_progress)
        self.playback_engine.time_tick.connect(self._on_time_tick)
        self.playback_engine.show_completed.connect(self._on_show_done)
        self.playback_engine.frame_ready.connect(self._emit_frame)
        self.playback_engine.start()

    def _on_progress(self, pct: float):
        self.progress.setValue(int(pct))

    def _on_time_tick(self, elapsed: float, total: float):
        self._current_total = total
        self._update_time_readout(elapsed, total)

    def _on_show_done(self):
        if self.is_playing:
            self._next()

    def _emit_frame(self, universe: int, frame: bytes):
        # Forward to MainWindow via signal
        self.dmx_changed.emit(universe, frame)

    # -------- External API used by MainWindow --------
    def set_admin_mode(self, is_admin: bool):
        self._is_admin = is_admin
        # Toggle admin buttons
        if hasattr(self, "btn_edit"):
            self.btn_edit.setEnabled(self._is_admin)
        if hasattr(self, "btn_delete"):
            self.btn_delete.setEnabled(self._is_admin)

    # ------------- Header helpers -------------
    def _init_clock(self):
        self._ntp_offset = 0.0  # seconds, applied to displayed time
        self._clock = QTimer(self)
        self._clock.timeout.connect(self._update_clock_label)
        self._clock.start(1000)
        self._update_clock_label()

    def _tz(self):
        if ZoneInfo is None:
            return timezone.utc
        try:
            return ZoneInfo(self._timezones[self._tz_index])
        except Exception:
            return timezone.utc

    def _update_clock_label(self):
        # Get UTC time + NTP offset
        now_utc = datetime.now(timezone.utc).timestamp() + self._ntp_offset
        # Convert to selected timezone
        dt = datetime.fromtimestamp(now_utc, tz=self._tz())
        self.lbl_time.setText(dt.strftime("%Y-%m-%d %H:%M:%S"))

    def _set_timezone(self, timezone: str):
        """Set timezone directly from menu selection"""
        if timezone in self._timezones:
            self._tz_index = self._timezones.index(timezone)
            # Update timezone in config
            if self.config_manager:
                self.config_manager.set_app_config('ui.timezone', timezone)
                self.config_manager.save_configs()
            self._update_clock_label()

    def _cycle_timezone(self):
        self._tz_index = (self._tz_index + 1) % len(self._timezones)
        # Update timezone in config
        if self.config_manager:
            self.config_manager.set_app_config('ui.timezone', self._timezones[self._tz_index])
            self.config_manager.save_configs()
        self._update_clock_label()

    def _sync_ntp_once(self):
        # Simple SNTP query, adjust display offset only
        try:
            self._ntp_offset = self._query_ntp_offset('pool.ntp.org')
            self._update_clock_label()
            QMessageBox.information(self, "NTP", "Time synchronized (display only)")
        except Exception as e:
            QMessageBox.warning(self, "NTP", f"Failed to sync: {e}")

    @staticmethod
    def _query_ntp_offset(host: str, port: int = 123, timeout_s: float = 2.0) -> float:
        # Returns offset seconds to add to system UTC to match NTP time
        # SNTP v4 minimal client
        import time as _t
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.settimeout(timeout_s)
        try:
            # Construct request packet
            msg = b'\x1b' + 47 * b'\0'
            t0 = _t.time()
            client.sendto(msg, (host, port))
            data, _ = client.recvfrom(48)
            t3 = _t.time()
        finally:
            client.close()
        if len(data) < 48:
            raise RuntimeError("Invalid NTP response")
        # Transmit timestamp seconds in bytes 40..43 and fraction 44..47
        def _ts(sec_bytes, frac_bytes):
            sec = struct.unpack('!I', sec_bytes)[0]
            frac = struct.unpack('!I', frac_bytes)[0]
            return sec + frac / 2**32
        # NTP epoch (1900) to Unix epoch (1970) offset
        NTP_DELTA = 2208988800
        tx = _ts(data[40:44], data[44:48]) - NTP_DELTA  # server transmit time (t2)
        # Approx round-trip: offset = (t2 - (t0 + t3)/2)
        offset = tx - (t0 + t3) / 2
        return float(offset)

    def _select_background(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Background Image",
                                              "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if not path:
            return
        # Apply and persist
        self._apply_background_path(path)
        if self.config_manager:
            self.config_manager.set_app_config('ui.background_path', path)
            self.config_manager.save_configs()

    def _apply_saved_background(self):
        if not self.config_manager:
            return
        path = self.config_manager.get_app_config('ui.background_path', '')
        if path:
            self._apply_background_path(path)

    def _apply_background_path(self, path: str):
        # Use stylesheet with objectName
        # Note: use url() with local path; spaces need quotes
        safe = path.replace('"', '\\"')
        self.setStyleSheet(
            f"#ShowManagerRoot {{ background-image: url(\"{safe}\"); background-position: center; background-repeat: no-repeat; }}"
        )

    def _edit_project_name(self):
        if not self._is_admin:
            QMessageBox.information(self, "Admin", "Admin mode required to edit project name")
            return
        text, ok = QInputDialog.getText(self, "Project Name", "Enter project name:", text=self.project_name)
        if ok and text:
            self.project_name = text
            self.lbl_project.setText(f"Project: {self.project_name}")
            if self.config_manager:
                self.config_manager.set_app_config('project.name', self.project_name)
                self.config_manager.save_configs()

    # ------- Time readout for current playing show -------
    def _estimate_total_duration(self, data: dict) -> float:
        try:
            return float(sum(float(s.get('duration', 0)) for s in data.get('scenes', [])))
        except Exception:
            return 0.0

    def _update_time_readout(self, elapsed: float, total: float):
        def fmt(s: float) -> str:
            s = max(0, int(round(s)))
            return f"{s//60:02d}:{s%60:02d}"
        remaining = max(0.0, float(total) - float(elapsed))
        self.time_readout.setText(f"{fmt(elapsed)} / {fmt(total)}  (−{fmt(remaining)})")

    # ------------- Scheduler -------------
    def _schedule_selected(self):
        # Collect selected shows from library in visible order
        rows = sorted({it.row() for it in self.table.selectedItems()})
        if not rows:
            QMessageBox.warning(self, "Scheduler", "Select shows in the library to schedule")
            return
        names = [self.table.item(r, 0).text() for r in rows]
        dt = self.sched_dt.dateTime().toPyDateTime()
        tz = self._timezones[self._tz_index]
        entry = {"dt": dt.isoformat(sep=' ', timespec='minutes'), "tz": tz, "shows": names, "done": False}
        self._add_schedule_entry(entry)

    def _add_schedule_entry(self, entry: dict):
        text = f"{entry['dt']} [{entry['tz']}] - " + " -> ".join(entry['shows'])
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, entry)
        self.sched_list.addItem(item)
        # Optionally persist later via config_manager

    def _scheduler_tick(self):
        if not self.chk_scheduler_enabled.isChecked():
            return
        now_utc = datetime.now(timezone.utc)
        for i in range(self.sched_list.count()):
            item = self.sched_list.item(i)
            entry = item.data(Qt.ItemDataRole.UserRole)
            if not entry or entry.get('done'):
                continue
            try:
                tzname = entry.get('tz', 'UTC')
                tz = ZoneInfo(tzname) if ZoneInfo else timezone.utc
                dt_local = datetime.strptime(entry['dt'], "%Y-%m-%d %H:%M")
                dt_target = dt_local.replace(tzinfo=tz).astimezone(timezone.utc)
            except Exception:
                continue
            if now_utc >= dt_target:
                # Execute: load shows and play
                shows = [s for s in entry.get('shows', []) if s in self.shows_data]
                if shows:
                    self.playlist.clear()
                    for name in shows:
                        self.playlist.addItem(name)
                    self.current_show_index = 0
                    self._start_playback()
                entry['done'] = True
                item.setData(Qt.ItemDataRole.UserRole, entry)
                item.setText(item.text() + "  [DONE]")
    
    def _remove_selected_schedule(self):
        """Remove selected schedule entry"""
        current_row = self.sched_list.currentRow()
        if current_row >= 0:
            self.sched_list.takeItem(current_row)
        else:
            QMessageBox.warning(self, "Remove Schedule", "Please select a schedule entry to remove")
    
    def _clear_all_schedules(self):
        """Clear all schedule entries"""
        if self.sched_list.count() == 0:
            QMessageBox.information(self, "Clear Schedules", "Schedule list is already empty")
            return
        
        reply = QMessageBox.question(
            self,
            "Clear All Schedules",
            f"Are you sure you want to clear all {self.sched_list.count()} schedule(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.sched_list.clear()
            QMessageBox.information(self, "Clear Schedules", "All schedules cleared")

    # ------------- Admin ops -------------
    def _selected_show_name(self) -> str | None:
        items = self.table.selectedItems()
        if not items:
            return None
        return self.table.item(items[0].row(), 0).text()

    def _edit_show(self):
        if not self._is_admin:
            QMessageBox.warning(
                self,
                "License Required",
                "⚠️ Admin license required to edit shows.\n\n"
                "Trial users can only play shows.\n"
                "Please activate a license to unlock admin features."
            )
            return
        name = self._selected_show_name()
        if not name:
            QMessageBox.warning(self, "Edit Show", "Select a show to edit")
            return
        QMessageBox.information(self, "Edit Show", f"Editing show '{name}' is not implemented yet.")

    def _delete_show(self):
        if not self._is_admin:
            QMessageBox.warning(
                self, 
                "License Required", 
                "⚠️ Admin license required to delete shows.\n\n"
                "Trial users can only play shows.\n"
                "Please activate a license to unlock admin features."
            )
            return
        name = self._selected_show_name()
        if not name:
            QMessageBox.warning(self, "Delete Show", "Select a show to delete")
            return
        path = Path("data/shows") / f"{name}.json"
        if not path.exists():
            QMessageBox.warning(self, "Delete Show", f"Show file not found: {path.name}")
            return
        from PyQt6.QtWidgets import QMessageBox as _QMB
        if _QMB.question(self, "Confirm", f"Delete show '{name}'?",
                         _QMB.StandardButton.Yes | _QMB.StandardButton.No) == _QMB.StandardButton.Yes:
            try:
                path.unlink()
                self._load_shows()
                # Remove from playlist if present
                for i in reversed(range(self.playlist.count())):
                    if self.playlist.item(i).text() == name:
                        self.playlist.takeItem(i)
                QMessageBox.information(self, "Delete Show", f"Deleted '{name}'")
            except Exception as e:
                QMessageBox.critical(self, "Delete Show", f"Failed to delete: {e}")


class SimplePlaybackEngine(QThread):
    """Very simple scene player: iterates scenes and emits DMX frames"""

    progress_updated = pyqtSignal(float)
    time_tick = pyqtSignal(float, float)  # elapsed, total seconds
    show_completed = pyqtSignal()
    frame_ready = pyqtSignal(int, bytes)

    def __init__(self, show_data: dict):
        super().__init__()
        self._data = show_data
        self._running = False
        self._paused = False
        self._start_ts = 0.0

    def run(self):
        self._running = True
        self._paused = False
        self._start_ts = time.time()

        scenes = self._data.get("scenes", [])
        total = float(self._data.get("duration", 0)) or self._estimate_total(scenes)

        elapsed_accum = 0.0
        for scene in scenes:
            if not self._running:
                break
            while self._paused and self._running:
                time.sleep(0.05)

            # Emit DMX for this scene
            dmx_map: dict = scene.get("dmx_data", {})
            for uni_str, arr in dmx_map.items():
                try:
                    uni = int(uni_str)
                except Exception:
                    continue
                frame = self._to_512_bytes(arr)
                if frame is not None:
                    self.frame_ready.emit(uni, frame)

            # Update progress periodically during scene
            scene_dur = float(scene.get("duration", 1.0))
            t0 = time.time()
            while self._running and not self._paused:
                dt = time.time() - t0
                if dt >= scene_dur:
                    break
                elapsed = elapsed_accum + dt
                self.time_tick.emit(elapsed, total)
                self.progress_updated.emit(min(100.0, (elapsed / total) * 100.0 if total > 0 else 0.0))
                time.sleep(0.2)

            elapsed_accum += scene_dur
            self.time_tick.emit(elapsed_accum, total)
            self.progress_updated.emit(min(100.0, (elapsed_accum / total) * 100.0 if total > 0 else 0.0))

        if self._running:
            self.progress_updated.emit(100.0)
            self.show_completed.emit()

    def pause(self):
        self._paused = True

    def stop(self):
        self._running = False
        try:
            self.wait(1000)
        except Exception:
            pass

    @staticmethod
    def _to_512_bytes(arr) -> bytes | None:
        """Convert a list/int dict to 512 bytes frame if possible"""
        try:
            if isinstance(arr, list):
                buf = bytes(int(max(0, min(255, v))) for v in (arr + [0] * (512 - len(arr))))[:512]
                return buf
        except Exception:
            return None
        return None

    @staticmethod
    def _estimate_total(scenes) -> float:
        try:
            return float(sum(float(s.get('duration', 0)) for s in scenes))
        except Exception:
            return 0.0


class BinaryPlaybackEngine(QThread):
    """Binary DMX show player using DMXPlayer for .dmxrec files"""

    progress_updated = pyqtSignal(float)
    time_tick = pyqtSignal(float, float)  # elapsed, total seconds
    show_completed = pyqtSignal()
    frame_ready = pyqtSignal(int, bytes)

    def __init__(self, binary_file_path: str, show_duration: float = 0):
        super().__init__()
        self.binary_file_path = binary_file_path
        self.show_duration = show_duration
        self._running = False
        self._paused = False
        self.dmx_player = None

    def run(self):
        if DMXPlayer is None:
            print("DMXPlayer not available - cannot play binary show")
            return

        self._running = True
        self._paused = False
        start_time = time.monotonic()

        try:
            # Open binary recording
            self.dmx_player = DMXPlayer(self.binary_file_path, buffer_size=100)
            if not self.dmx_player.open():
                print(f"Failed to open binary file: {self.binary_file_path}")
                return

            # Get recording info
            info = self.dmx_player.get_info()
            total_duration = self.show_duration or info.get('duration', 0)
            fps = info.get('fps', 40.0)
            frame_interval = 1.0 / fps

            print(f"Playing binary show: {info['frame_count']} frames @ {fps} FPS, {total_duration:.1f}s")

            # Start multithreaded playback
            if not self.dmx_player.start_playback():
                print("Failed to start DMX playback")
                return

            # Playback loop
            next_frame_time = time.monotonic()
            frames_played = 0

            while self._running:
                # Handle pause
                while self._paused and self._running:
                    time.sleep(0.05)
                    next_frame_time = time.monotonic()  # Reset timing after pause
                    continue

                if not self._running:
                    break

                # Get next frame from buffer
                frame = self.dmx_player.get_next_frame(timeout=0.1)
                if frame is None:
                    # End of recording
                    break

                # Emit frame
                self.frame_ready.emit(frame.universe, frame.data)
                frames_played += 1

                # Calculate progress and timing
                current_time = time.monotonic()
                elapsed = current_time - start_time
                
                if total_duration > 0:
                    progress = min(100.0, (elapsed / total_duration) * 100.0)
                    self.progress_updated.emit(progress)
                
                self.time_tick.emit(elapsed, total_duration)

                # Frame rate control
                next_frame_time += frame_interval
                sleep_time = next_frame_time - current_time
                if sleep_time > 0:
                    time.sleep(sleep_time)
                elif sleep_time < -0.1:  # If we're more than 100ms behind, reset timing
                    next_frame_time = current_time

            if self._running:
                self.progress_updated.emit(100.0)
                self.show_completed.emit()

        except Exception as e:
            print(f"Error during binary playback: {e}")
        finally:
            if self.dmx_player:
                try:
                    self.dmx_player.stop_playback()
                    self.dmx_player.close()
                except Exception as e:
                    print(f"Error closing DMX player: {e}")
                self.dmx_player = None

    def pause(self):
        self._paused = True

    def stop(self):
        self._running = False
        if self.dmx_player:
            try:
                self.dmx_player.stop_playback()
            except Exception:
                pass
        try:
            self.wait(2000)  # Wait up to 2 seconds for thread to finish
        except Exception:
            pass
