"""
Flask Web Server cho MP3 Upload + REST API.

Webserver để upload MP3 files, quản lý shows, và cung cấp REST API
cho AI_DMX_Autopilot trao đổi data (Phase 2 SYNC_PLAN).

Wing: code_chronicles
Topic: webserver
Last Updated: 2026-05-02
"""

import logging
import os
import threading
from pathlib import Path
from flask import Flask, request, render_template_string, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import mutagen
from mutagen.mp3 import MP3
from mutagen.id3 import ID3NoHeaderError

logger = logging.getLogger(__name__)

class MP3UploadServer:
    """Flask server cho MP3 upload"""
    
    def __init__(self, config_manager, show_manager):
        self.config_manager = config_manager
        self.show_manager = show_manager
        
        self.app = Flask(__name__)
        self.app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB default
        
        # Configure upload settings
        raw_upload_path = config_manager.get_app_config('webserver.upload_path', 'data/music')
        self.upload_path = self._resolve_upload_path(raw_upload_path)
        self.upload_path.mkdir(parents=True, exist_ok=True)
        
        self.allowed_extensions = {'mp3', 'wav', 'flac', 'm4a', 'ogg'}
        
        self.setup_routes()

        # Register API Blueprint (Phase 2 — SYNC_PLAN)
        from webserver.api import register_api_blueprint
        register_api_blueprint(
            self.app,
            show_manager=show_manager,
            config_manager=config_manager,
        )

        self.server_thread = None
        self.is_running = False

    def _resolve_upload_path(self, configured_path: str) -> Path:
        """Resolve upload path to a writable location.

        Relative paths are anchored under the app data directory to avoid
        permission issues when running from protected install locations.
        """
        path = Path(configured_path)

        if not path.is_absolute():
            # ConfigManager uses: <AppData>/DMX Master LTS/config
            # We anchor relative upload paths at: <AppData>/DMX Master LTS
            app_root = Path(self.config_manager.config_dir).parent
            path = app_root / path

        try:
            path.mkdir(parents=True, exist_ok=True)
            return path
        except PermissionError:
            fallback = Path(self.config_manager.config_dir).parent / "data" / "music"
            fallback.mkdir(parents=True, exist_ok=True)
            logger.warning(
                "Upload path '%s' is not writable, falling back to '%s'",
                configured_path,
                fallback,
            )
            return fallback
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main upload page"""
            return render_template_string(self.get_upload_template())
        
        @self.app.route('/upload', methods=['POST'])
        def upload_file():
            """Handle file upload"""
            try:
                if 'file' not in request.files:
                    return jsonify({'error': 'No file provided'}), 400
                
                file = request.files['file']
                
                if file.filename == '':
                    return jsonify({'error': 'No file selected'}), 400
                
                if not self.allowed_file(file.filename):
                    return jsonify({'error': 'File type not allowed'}), 400
                
                # Get show name from form data
                show_name = request.form.get('show', 'default')
                
                # Save file
                result = self.save_uploaded_file(file, show_name)
                
                if result['success']:
                    return jsonify(result), 200
                else:
                    return jsonify(result), 500
                    
            except RequestEntityTooLarge:
                return jsonify({'error': 'File too large'}), 413
            except Exception as e:
                logger.error(f"Upload error: {e}")
                return jsonify({'error': str(e)}), 500
        
        # NOTE: /api/shows now handled by api.py Blueprint (Phase 2)
        # Frontend compat: blueprint returns full metadata, JS extracts .name
        
        @self.app.route('/api/files/<show_name>')
        def get_show_files(show_name):
            """Get files in show folder"""
            try:
                music_folder = self.show_manager.get_show_music_folder(show_name)
                
                files = []
                if music_folder.exists():
                    for file_path in music_folder.glob("*"):
                        if file_path.is_file() and self.allowed_file(file_path.name):
                            # Get file metadata
                            metadata = self.get_file_metadata(file_path)
                            files.append({
                                'name': file_path.name,
                                'size': file_path.stat().st_size,
                                'metadata': metadata
                            })
                
                return jsonify({'files': files})
            except Exception as e:
                logger.error(f"Error getting show files: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/download/<show_name>/<filename>')
        def download_file(show_name, filename):
            """Download file from show folder"""
            try:
                safe_filename = secure_filename(filename)
                if not safe_filename:
                    return jsonify({'error': 'Invalid filename'}), 400
                music_folder = self.show_manager.get_show_music_folder(show_name)
                return send_from_directory(music_folder, safe_filename)
            except Exception as e:
                logger.error(f"Download error: {e}")
                return jsonify({'error': str(e)}), 404
        
        @self.app.route('/delete/<show_name>/<filename>', methods=['DELETE'])
        def delete_file(show_name, filename):
            """Delete file from show folder"""
            try:
                music_folder = self.show_manager.get_show_music_folder(show_name)
                file_path = music_folder / secure_filename(filename)
                
                if file_path.exists() and file_path.is_file():
                    file_path.unlink()
                    return jsonify({'success': True, 'message': f'File {filename} deleted'})
                else:
                    return jsonify({'error': 'File not found'}), 404
                    
            except Exception as e:
                logger.error(f"Delete error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.errorhandler(RequestEntityTooLarge)
        def handle_large_file(e):
            return jsonify({'error': 'File too large'}), 413
        
        @self.app.errorhandler(Exception)
        def handle_error(e):
            logger.error(f"Server error: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    def allowed_file(self, filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def save_uploaded_file(self, file, show_name):
        """Save uploaded file"""
        try:
            filename = secure_filename(file.filename)
            
            # Get destination folder
            if show_name and show_name != 'default':
                dest_folder = self.show_manager.get_show_music_folder(show_name)
            else:
                dest_folder = self.upload_path
            
            dest_folder.mkdir(parents=True, exist_ok=True)
            
            # Check if file already exists
            file_path = dest_folder / filename
            if file_path.exists():
                # Add counter to filename
                name, ext = filename.rsplit('.', 1)
                counter = 1
                while file_path.exists():
                    filename = f"{name}_{counter}.{ext}"
                    file_path = dest_folder / filename
                    counter += 1
            
            # Save file
            file.save(str(file_path))
            
            # Get metadata
            metadata = self.get_file_metadata(file_path)
            
            # Add to show playlist if current show exists
            if self.show_manager.current_show and show_name == self.show_manager.current_show.metadata.name:
                from show.manager import PlaylistItem
                
                playlist_item = PlaylistItem(
                    file_path=str(file_path),
                    title=metadata.get('title', filename),
                    artist=metadata.get('artist', ''),
                    duration=metadata.get('duration', 0.0)
                )
                
                self.show_manager.add_playlist_item(playlist_item)
            
            logger.info(f"File uploaded: {file_path}")
            
            return {
                'success': True,
                'message': f'File {filename} uploaded successfully',
                'filename': filename,
                'show': show_name,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_file_metadata(self, file_path):
        """Get audio file metadata"""
        try:
            audio_file = mutagen.File(str(file_path))
            
            if audio_file is None:
                return {'title': file_path.stem, 'artist': '', 'duration': 0.0}
            
            # Get basic info
            title = str(audio_file.get('TIT2', [file_path.stem])[0]) if 'TIT2' in audio_file else file_path.stem
            artist = str(audio_file.get('TPE1', [''])[0]) if 'TPE1' in audio_file else ''
            album = str(audio_file.get('TALB', [''])[0]) if 'TALB' in audio_file else ''
            duration = getattr(audio_file, 'info', None)
            duration = duration.length if duration else 0.0
            
            return {
                'title': title,
                'artist': artist,
                'album': album,
                'duration': duration,
                'bitrate': getattr(audio_file.info, 'bitrate', 0) if hasattr(audio_file, 'info') else 0,
                'channels': getattr(audio_file.info, 'channels', 0) if hasattr(audio_file, 'info') else 0
            }
            
        except Exception as e:
            logger.warning(f"Failed to get metadata from {file_path}: {e}")
            return {'title': file_path.stem, 'artist': '', 'duration': 0.0}
    
    def get_upload_template(self):
        """HTML template for upload page"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Art-Net Controller - Music Upload</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #2c3e50, #3498db);
            color: white;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            color: #ecf0f1;
        }
        
        .header p {
            color: #bdc3c7;
            font-size: 1.1em;
        }
        
        .upload-section {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            border: 2px dashed #3498db;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .upload-section:hover {
            border-color: #2ecc71;
            background: rgba(255, 255, 255, 0.08);
        }
        
        .file-input {
            display: none;
        }
        
        .upload-button {
            background: linear-gradient(135deg, #3498db, #2ecc71);
            border: none;
            color: white;
            padding: 15px 30px;
            font-size: 1.1em;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s ease;
            margin: 10px;
        }
        
        .upload-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }
        
        .show-selector {
            margin: 20px 0;
        }
        
        .show-selector select {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid #3498db;
            border-radius: 10px;
            color: white;
            padding: 10px 15px;
            font-size: 1em;
            min-width: 200px;
        }
        
        .show-selector option {
            background: #2c3e50;
            color: white;
        }
        
        .file-list {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 20px;
            margin-top: 20px;
        }
        
        .file-item {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .file-info {
            flex: 1;
        }
        
        .file-name {
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .file-meta {
            font-size: 0.9em;
            color: #bdc3c7;
        }
        
        .file-actions button {
            background: #e74c3c;
            border: none;
            color: white;
            padding: 8px 15px;
            border-radius: 5px;
            cursor: pointer;
            margin-left: 5px;
        }
        
        .file-actions button:hover {
            background: #c0392b;
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
            display: none;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #3498db, #2ecc71);
            width: 0%;
            transition: width 0.3s ease;
        }
        
        .message {
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
            display: none;
        }
        
        .message.success {
            background: rgba(46, 204, 113, 0.2);
            border: 1px solid #2ecc71;
        }
        
        .message.error {
            background: rgba(231, 76, 60, 0.2);
            border: 1px solid #e74c3c;
        }
        
        .drag-over {
            border-color: #2ecc71 !important;
            background: rgba(46, 204, 113, 0.1) !important;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎵 Music Upload</h1>
            <p>Upload MP3 files to your Art-Net Controller shows</p>
        </div>
        
        <div class="upload-section" id="uploadSection">
            <h3>📁 Drop files here or click to browse</h3>
            <p>Supported formats: MP3, WAV, FLAC, M4A, OGG</p>
            
            <div class="show-selector">
                <label for="showSelect">Select Show:</label>
                <select id="showSelect">
                    <option value="default">Default</option>
                </select>
            </div>
            
            <input type="file" id="fileInput" class="file-input" multiple accept=".mp3,.wav,.flac,.m4a,.ogg">
            <button class="upload-button" onclick="document.getElementById('fileInput').click()">
                Choose Files
            </button>
        </div>
        
        <div class="progress-bar" id="progressBar">
            <div class="progress-fill" id="progressFill"></div>
        </div>
        
        <div class="message" id="message"></div>
        
        <div class="file-list" id="fileList">
            <h3>📋 Current Show Files</h3>
            <div id="fileItems"></div>
        </div>
    </div>
    
    <script>
        let currentShow = 'default';
        
        // Load shows (API returns full metadata, extract name)
        fetch('/api/shows')
            .then(response => response.json())
            .then(data => {
                const select = document.getElementById('showSelect');
                data.shows.forEach(show => {
                    const name = typeof show === 'object' ? show.name : show;
                    const option = document.createElement('option');
                    option.value = name;
                    option.textContent = name;
                    select.appendChild(option);
                });
            })
            .catch(error => console.error('Error loading shows:', error));
        
        // Show selection change
        document.getElementById('showSelect').addEventListener('change', function() {
            currentShow = this.value;
            loadShowFiles();
        });
        
        // File input change
        document.getElementById('fileInput').addEventListener('change', function() {
            handleFiles(this.files);
        });
        
        // Drag and drop
        const uploadSection = document.getElementById('uploadSection');
        
        uploadSection.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('drag-over');
        });
        
        uploadSection.addEventListener('dragleave', function(e) {
            e.preventDefault();
            this.classList.remove('drag-over');
        });
        
        uploadSection.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('drag-over');
            handleFiles(e.dataTransfer.files);
        });
        
        function handleFiles(files) {
            Array.from(files).forEach(file => {
                uploadFile(file);
            });
        }
        
        function uploadFile(file) {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('show', currentShow);
            
            const progressBar = document.getElementById('progressBar');
            const progressFill = document.getElementById('progressFill');
            
            progressBar.style.display = 'block';
            
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                progressBar.style.display = 'none';
                
                if (data.success || data.message) {
                    showMessage(data.message || 'Upload successful', 'success');
                    loadShowFiles();
                } else {
                    showMessage(data.error || 'Upload failed', 'error');
                }
            })
            .catch(error => {
                progressBar.style.display = 'none';
                showMessage('Upload failed: ' + error.message, 'error');
            });
        }
        
        function loadShowFiles() {
            fetch(`/api/files/${currentShow}`)
                .then(response => response.json())
                .then(data => {
                    const fileItems = document.getElementById('fileItems');
                    fileItems.innerHTML = '';
                    
                    if (data.files && data.files.length > 0) {
                        data.files.forEach(file => {
                            const fileDiv = document.createElement('div');
                            fileDiv.className = 'file-item';
                            
                            const metadata = file.metadata || {};
                            const duration = metadata.duration ? formatDuration(metadata.duration) : 'Unknown';
                            const size = formatFileSize(file.size);
                            
                            fileDiv.innerHTML = `
                                <div class="file-info">
                                    <div class="file-name">${file.name}</div>
                                    <div class="file-meta">
                                        ${metadata.title || file.name} - ${metadata.artist || 'Unknown Artist'}<br>
                                        Duration: ${duration} | Size: ${size}
                                    </div>
                                </div>
                                <div class="file-actions">
                                    <button onclick="downloadFile('${file.name}')">Download</button>
                                    <button onclick="deleteFile('${file.name}')">Delete</button>
                                </div>
                            `;
                            
                            fileItems.appendChild(fileDiv);
                        });
                    } else {
                        fileItems.innerHTML = '<p>No files in this show</p>';
                    }
                })
                .catch(error => {
                    console.error('Error loading files:', error);
                });
        }
        
        function downloadFile(filename) {
            window.location.href = `/download/${currentShow}/${filename}`;
        }
        
        function deleteFile(filename) {
            if (confirm(`Are you sure you want to delete ${filename}?`)) {
                fetch(`/delete/${currentShow}/${filename}`, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showMessage(data.message, 'success');
                        loadShowFiles();
                    } else {
                        showMessage(data.error || 'Delete failed', 'error');
                    }
                })
                .catch(error => {
                    showMessage('Delete failed: ' + error.message, 'error');
                });
            }
        }
        
        function showMessage(text, type) {
            const message = document.getElementById('message');
            message.textContent = text;
            message.className = `message ${type}`;
            message.style.display = 'block';
            
            setTimeout(() => {
                message.style.display = 'none';
            }, 5000);
        }
        
        function formatDuration(seconds) {
            const mins = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return `${mins}:${secs.toString().padStart(2, '0')}`;
        }
        
        function formatFileSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        }
        
        // Load initial files
        loadShowFiles();
    </script>
</body>
</html>
        '''
    
    def start_server(self):
        """Start Flask server"""
        if self.is_running:
            return True
        
        try:
            config = self.config_manager.get_app_config('webserver', {})
            host = config.get('host', '0.0.0.0')
            port = config.get('port', 8080)
            
            # Update max file size
            max_size = config.get('max_file_size', 50) * 1024 * 1024
            self.app.config['MAX_CONTENT_LENGTH'] = max_size
            
            def run_server():
                self.app.run(
                    host=host,
                    port=port,
                    debug=False,
                    use_reloader=False,
                    threaded=True
                )
            
            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
            
            self.is_running = True
            
            logger.info(f"Web server started on http://{host}:{port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start web server: {e}")
            return False
    
    def stop_server(self):
        """Stop Flask server"""
        if not self.is_running:
            return
        
        # Flask doesn't have a built-in way to stop gracefully
        # In a production environment, you would use a WSGI server like Gunicorn
        self.is_running = False
        logger.info("Web server stop requested")
    
    def get_server_url(self):
        """Get server URL"""
        config = self.config_manager.get_app_config('webserver', {})
        host = config.get('host', '0.0.0.0')
        port = config.get('port', 8080)
        
        # Replace 0.0.0.0 with localhost for display
        if host == '0.0.0.0':
            host = 'localhost'
        
        return f"http://{host}:{port}"