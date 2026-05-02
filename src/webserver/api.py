"""REST API Blueprint cho ArtNetController — Phase 2 SYNC_PLAN.

Cung cấp API endpoints để AI_DMX_Autopilot trao đổi data:
- Health check
- Shows CRUD (full metadata)
- Export .dmxrec → CSV
- Import CSV → .dmxrec
- Recordings listing
- Fixture database (placeholder)

Wing: code_chronicles
Topic: artnet_api
Last Updated: 2026-05-02 11:27
"""

import functools
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional

from flask import Blueprint, request, jsonify, send_file, current_app

logger = logging.getLogger(__name__)

# ── DMX_Shared_Lib import ──
_SHARED_LIB_PATH = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..', 'DMX_Shared_Lib'
))
if _SHARED_LIB_PATH not in sys.path:
    sys.path.insert(0, _SHARED_LIB_PATH)

from dmx_data.binary_reader import DMXRecReader
from dmx_data.csv_converter import dmxrec_to_csv, csv_to_dmxrec

# ── Version ──
from version import get_version

# Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')


# ──────────────────────────────────────────────
# Authentication
# ──────────────────────────────────────────────

def _get_expected_api_key() -> Optional[str]:
    """Lấy API key từ config hoặc env variable."""
    return os.environ.get('ARTNET_API_KEY', None)


def require_api_key(f):
    """Decorator: yêu cầu X-API-Key header nếu API key được cấu hình."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        expected = _get_expected_api_key()
        if expected is None:
            # No API key configured → open access (local network only)
            return f(*args, **kwargs)

        provided = request.headers.get('X-API-Key', '')
        if provided != expected:
            return jsonify({'error': 'Unauthorized — invalid or missing API key'}), 401
        return f(*args, **kwargs)
    return decorated


def _get_show_manager():
    """Lấy ShowManager từ app context."""
    return current_app.config.get('SHOW_MANAGER')


def _get_config_manager():
    """Lấy ConfigManager từ app context."""
    return current_app.config.get('CONFIG_MANAGER')


def _get_shows_path() -> Path:
    """Lấy đường dẫn shows directory."""
    sm = _get_show_manager()
    if sm:
        return sm.shows_path
    return Path('data/shows')


def _get_recordings_path() -> Path:
    """Lấy đường dẫn recordings directory."""
    config = _get_config_manager()
    if config:
        raw = config.get_app_config('recording.path', 'data/show_resources')
    else:
        raw = 'data/show_resources'
    p = Path(raw)
    if not p.is_absolute():
        p = Path(os.getcwd()) / p
    return p


def _find_dmxrec_for_show(show_name: str) -> Optional[Path]:
    """Tìm file .dmxrec tương ứng với show."""
    shows_path = _get_shows_path()

    # 1) Check binary_file trong show JSON metadata
    show_json = shows_path / f"{show_name}.json"
    if show_json.exists():
        import json
        try:
            with open(show_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            binary_name = data.get('metadata', {}).get('binary_file')
            if binary_name:
                candidate = shows_path / binary_name
                if candidate.exists():
                    return candidate
        except Exception:
            pass

    # 2) Scan recordings directory
    rec_path = _get_recordings_path()
    if rec_path.exists():
        for ext in ('*.dmxrec',):
            for f in sorted(rec_path.glob(ext)):
                if show_name.lower() in f.stem.lower():
                    return f

    # 3) Fallback: same-name .dmxrec trong shows dir
    candidate = shows_path / f"{show_name}.dmxrec"
    if candidate.exists():
        return candidate

    return None


# ──────────────────────────────────────────────
# Health
# ──────────────────────────────────────────────

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'version': get_version(),
        'service': 'ArtNetController',
    })


# ──────────────────────────────────────────────
# Shows — Full CRUD
# ──────────────────────────────────────────────

@api_bp.route('/shows', methods=['GET'])
@require_api_key
def list_shows():
    """List tất cả shows với full metadata."""
    sm = _get_show_manager()
    if not sm:
        return jsonify({'error': 'ShowManager not available'}), 503

    try:
        shows = sm.get_show_list()
        return jsonify({'shows': shows})
    except Exception as e:
        logger.error(f"Error listing shows: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/shows/<show_name>', methods=['GET'])
@require_api_key
def get_show_detail(show_name):
    """Get show metadata + binary info."""
    sm = _get_show_manager()
    if not sm:
        return jsonify({'error': 'ShowManager not available'}), 503

    shows_path = _get_shows_path()

    # Try JSON first
    show_json = shows_path / f"{show_name}.json"
    if not show_json.exists():
        # Try finding by partial name
        candidates = list(shows_path.glob("*.json"))
        for c in candidates:
            import json
            try:
                with open(c, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if data.get('metadata', {}).get('name') == show_name:
                    show_json = c
                    break
            except Exception:
                continue

    if not show_json.exists():
        return jsonify({'error': f'Show not found: {show_name}'}), 404

    try:
        import json
        with open(show_json, 'r', encoding='utf-8') as f:
            show_data = json.load(f)

        metadata = show_data.get('metadata', {})
        binary_path = _find_dmxrec_for_show(show_name)

        result = {
            'name': metadata.get('name', show_name),
            'metadata': metadata,
            'scene_count': len(show_data.get('scenes', [])),
            'playlist_count': len(show_data.get('playlist', [])),
            'has_binary_recording': binary_path is not None,
            'binary_file': str(binary_path) if binary_path else None,
            'show_file': str(show_json),
        }

        # Add binary recording stats if available
        if binary_path and binary_path.exists():
            try:
                reader = DMXRecReader(str(binary_path))
                header = reader.read_header()
                if header:
                    result['recording'] = {
                        'fps': header.fps,
                        'frame_count': header.frame_count,
                        'file_size': binary_path.stat().st_size,
                    }
            except Exception:
                pass

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting show detail: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/shows/<show_name>/download', methods=['GET'])
@require_api_key
def download_show(show_name):
    """Download .dmxrec binary file."""
    binary_path = _find_dmxrec_for_show(show_name)
    if not binary_path or not binary_path.exists():
        return jsonify({'error': f'No binary recording found for show: {show_name}'}), 404

    try:
        return send_file(
            str(binary_path),
            as_attachment=True,
            download_name=binary_path.name,
            mimetype='application/octet-stream',
        )
    except Exception as e:
        logger.error(f"Error downloading show: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/shows/<show_name>/export-csv', methods=['POST'])
@require_api_key
def export_show_csv(show_name):
    """Convert .dmxrec → CSV và trả về file CSV."""
    binary_path = _find_dmxrec_for_show(show_name)
    if not binary_path or not binary_path.exists():
        return jsonify({'error': f'No binary recording found for show: {show_name}'}), 404

    try:
        # Parse optional universe filter
        universes = None
        uni_param = request.args.get('universes')
        if uni_param:
            universes = [int(u.strip()) for u in uni_param.split(',')]

        # Convert to temp CSV
        tmp = tempfile.NamedTemporaryFile(
            suffix='.csv', delete=False, prefix=f'{show_name}_'
        )
        tmp_path = tmp.name
        tmp.close()

        stats = dmxrec_to_csv(binary_path, tmp_path, universes=universes)

        return send_file(
            tmp_path,
            as_attachment=True,
            download_name=f'{show_name}.csv',
            mimetype='text/csv',
        )
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/shows/import', methods=['POST'])
@require_api_key
def import_show():
    """Import CSV file từ AI_DMX_Autopilot → tạo .dmxrec + show JSON."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    show_name = request.form.get('name', Path(file.filename).stem)
    fps = float(request.form.get('fps', 40.0))

    try:
        # Save uploaded CSV to temp
        tmp_csv = tempfile.NamedTemporaryFile(
            suffix='.csv', delete=False, prefix='import_'
        )
        file.save(tmp_csv.name)
        tmp_csv.close()

        # Determine output path
        recordings_path = _get_recordings_path()
        recordings_path.mkdir(parents=True, exist_ok=True)
        output_dmxrec = recordings_path / f"{show_name}.dmxrec"

        # Convert CSV → .dmxrec
        stats = csv_to_dmxrec(tmp_csv.name, str(output_dmxrec), fps=fps)

        # Clean up temp CSV
        Path(tmp_csv.name).unlink(missing_ok=True)

        # Optionally create show JSON
        sm = _get_show_manager()
        if sm:
            import json
            from datetime import datetime
            show_data = {
                'metadata': {
                    'name': show_name,
                    'description': f'Imported from AI_DMX_Autopilot',
                    'author': 'AI_DMX_Autopilot',
                    'created_date': datetime.now().isoformat(),
                    'modified_date': datetime.now().isoformat(),
                    'version': '1.0',
                    'duration': stats.get('frame_count', 0) / fps if fps > 0 else 0,
                    'bpm': 120.0,
                    'universes': stats.get('universes', []),
                    'binary_file': f"{show_name}.dmxrec",
                },
                'playlist': [],
                'scenes': [],
            }
            show_json_path = sm.shows_path / f"{show_name}.json"
            with open(show_json_path, 'w', encoding='utf-8') as f:
                json.dump(show_data, f, indent=2, ensure_ascii=False)

        result = {
            'status': 'ok',
            'show_name': show_name,
            'dmxrec_file': str(output_dmxrec),
            'frame_count': stats.get('frame_count', 0),
            'universes': stats.get('universes', []),
            'fps': fps,
        }
        return jsonify(result), 201

    except Exception as e:
        logger.error(f"Error importing show: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/shows/<show_name>', methods=['DELETE'])
@require_api_key
def delete_show(show_name):
    """Delete show (JSON + binary)."""
    sm = _get_show_manager()
    if not sm:
        return jsonify({'error': 'ShowManager not available'}), 503

    shows_path = _get_shows_path()

    # Find and delete show JSON
    show_json = shows_path / f"{show_name}.json"
    deleted = []

    if show_json.exists():
        show_json.unlink()
        deleted.append(str(show_json))

    # Delete associated binary
    binary_path = _find_dmxrec_for_show(show_name)
    if binary_path and binary_path.exists():
        binary_path.unlink()
        deleted.append(str(binary_path))

    if not deleted:
        return jsonify({'error': f'Show not found: {show_name}'}), 404

    return jsonify({'status': 'ok', 'deleted': deleted})


# ──────────────────────────────────────────────
# Recordings — List .dmxrec files
# ──────────────────────────────────────────────

@api_bp.route('/recordings', methods=['GET'])
@require_api_key
def list_recordings():
    """List tất cả .dmxrec files với metadata."""
    recordings_path = _get_recordings_path()
    if not recordings_path.exists():
        return jsonify({'recordings': []})

    recordings = []
    for f in sorted(recordings_path.glob("*.dmxrec")):
        try:
            info = {
                'name': f.stem,
                'file_path': str(f),
                'file_size': f.stat().st_size,
            }
            # Read header for FPS/frame count
            reader = DMXRecReader(str(f))
            header = reader.read_header()
            if header:
                info['fps'] = header.fps
                info['frame_count'] = header.frame_count
                info['duration'] = header.frame_count / header.fps if header.fps > 0 else 0
            recordings.append(info)
        except Exception as e:
            logger.warning(f"Failed to read recording {f}: {e}")
            recordings.append({
                'name': f.stem,
                'file_path': str(f),
                'file_size': f.stat().st_size,
                'error': str(e),
            })

    return jsonify({'recordings': recordings})


# ──────────────────────────────────────────────
# Fixtures — Placeholder
# ──────────────────────────────────────────────

@api_bp.route('/fixtures', methods=['GET'])
@require_api_key
def list_fixtures():
    """List fixture database (placeholder — chưa có fixture DB trong ArtNetController)."""
    return jsonify({
        'fixtures': [],
        'message': 'Fixture database not yet implemented in ArtNetController',
    })


def register_api_blueprint(app, show_manager=None, config_manager=None):
    """Register API blueprint vào Flask app.

    Args:
        app: Flask application instance.
        show_manager: ShowManager instance.
        config_manager: ConfigManager instance.
    """
    app.config['SHOW_MANAGER'] = show_manager
    app.config['CONFIG_MANAGER'] = config_manager
    app.register_blueprint(api_bp)
    logger.info("API Blueprint registered at /api")