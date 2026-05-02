"""Unit tests cho REST API Blueprint (Phase 2).

Tests cho /api/* endpoints: health, shows, export-csv, import, recordings.

Wing: code_chronicles
Topic: artnet_api_tests
Last Updated: 2026-05-02
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root, src, and DMX_Shared_Lib to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT.parent / 'DMX_Shared_Lib'))


@pytest.fixture
def app():
    """Tạo Flask test app với API blueprint."""
    from flask import Flask
    from webserver.api import register_api_blueprint
    from show.manager import ShowManager

    app = Flask(__name__)

    # Use temp directory for shows
    tmp_dir = tempfile.mkdtemp()
    sm = ShowManager(shows_path=os.path.join(tmp_dir, 'shows'))
    sm.shows_path.mkdir(parents=True, exist_ok=True)

    # Mock config manager
    config = MagicMock()
    config.get_app_config.return_value = os.path.join(tmp_dir, 'show_resources')

    register_api_blueprint(app, show_manager=sm, config_manager=config)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get('/api/health')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'ok'
        assert 'version' in data


class TestShowsEndpoints:
    def test_list_shows_empty(self, client):
        resp = client.get('/api/shows')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'shows' in data
        assert len(data['shows']) == 0

    def test_list_shows_with_data(self, client, app):
        # Create a test show JSON
        sm = app.config['SHOW_MANAGER']
        show_file = sm.shows_path / 'test_show.json'
        show_data = {
            'metadata': {'name': 'TestShow', 'description': 'test', 'author': ''},
            'playlist': [],
            'scenes': [],
        }
        with open(show_file, 'w') as f:
            json.dump(show_data, f)

        resp = client.get('/api/shows')
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data['shows']) == 1
        assert data['shows'][0]['name'] == 'TestShow'

    def test_get_show_detail_not_found(self, client):
        resp = client.get('/api/shows/nonexistent')
        assert resp.status_code == 404

    def test_get_show_detail(self, client, app):
        sm = app.config['SHOW_MANAGER']
        show_file = sm.shows_path / 'myshow.json'
        show_data = {
            'metadata': {'name': 'MyShow', 'description': '', 'author': ''},
            'playlist': [],
            'scenes': [{'name': 'S1', 'universe': 0, 'channels': {1: 128}}],
        }
        with open(show_file, 'w') as f:
            json.dump(show_data, f)

        resp = client.get('/api/shows/myshow')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['name'] == 'MyShow'
        assert data['scene_count'] == 1
        assert data['has_binary_recording'] is False


class TestRecordingsEndpoint:
    def test_list_recordings_empty(self, client):
        resp = client.get('/api/recordings')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['recordings'] == []


class TestFixturesEndpoint:
    def test_list_fixtures_placeholder(self, client):
        resp = client.get('/api/fixtures')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'fixtures' in data


class TestImportExport:
    def test_import_no_file(self, client):
        resp = client.post('/api/shows/import')
        assert resp.status_code == 400

    def test_export_csv_not_found(self, client):
        resp = client.post('/api/shows/nonexistent/export-csv')
        assert resp.status_code == 404

    def test_download_not_found(self, client):
        resp = client.get('/api/shows/nonexistent/download')
        assert resp.status_code == 404


class TestDeleteShow:
    def test_delete_not_found(self, client):
        resp = client.delete('/api/shows/nonexistent')
        assert resp.status_code == 404

    def test_delete_show(self, client, app):
        sm = app.config['SHOW_MANAGER']
        show_file = sm.shows_path / 'deleteme.json'
        with open(show_file, 'w') as f:
            json.dump({'metadata': {'name': 'DeleteMe'}, 'playlist': [], 'scenes': []}, f)

        resp = client.delete('/api/shows/deleteme')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'ok'
        assert not show_file.exists()


class TestAPIKeyAuth:
    @patch.dict(os.environ, {'ARTNET_API_KEY': 'test-secret'})
    def test_unauthorized_without_key(self, client):
        resp = client.get('/api/shows')
        assert resp.status_code == 401

    @patch.dict(os.environ, {'ARTNET_API_KEY': 'test-secret'})
    def test_authorized_with_key(self, client):
        resp = client.get('/api/shows', headers={'X-API-Key': 'test-secret'})
        assert resp.status_code == 200

    @patch.dict(os.environ, {'ARTNET_API_KEY': 'test-secret'})
    def test_wrong_key(self, client):
        resp = client.get('/api/shows', headers={'X-API-Key': 'wrong'})
        assert resp.status_code == 401