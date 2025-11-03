#!/usr/bin/env python3
"""
License Revocation Server
==========================
Simple Flask server to check if licenses have been revoked.

This server does NOT generate licenses (that's done offline with generate_license.py).
It only maintains a revocation list to allow you to remotely disable licenses.

Endpoints:
    POST /api/license/check_revoked
        - Check if a license is revoked
        - Request: {"license_id": "uuid", "device_id": "sha256"}
        - Response: {"valid": true/false, "reason": "..."}
    
    POST /api/license/revoke
        - Revoke a license (admin only)
        - Request: {"license_id": "uuid", "reason": "...", "admin_key": "..."}
        - Response: {"success": true/false}
    
    GET /api/license/list_revoked
        - List all revoked licenses (admin only)
        - Query: ?admin_key=...
        - Response: {"revoked_licenses": [...]}

Usage:
    python license_server.py
    
    Or with Gunicorn (production):
    gunicorn -w 4 -b 0.0.0.0:5000 license_server:app
"""

from flask import Flask, request, jsonify
import json
import logging
from datetime import datetime
from pathlib import Path

# === CONFIGURATION ===
ADMIN_KEY = "change-this-admin-key-in-production"  # Change this!
REVOCATION_DB = Path(__file__).parent / "revoked_licenses.json"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


def load_revoked_licenses():
    """Load revoked licenses from JSON file"""
    try:
        if REVOCATION_DB.exists():
            with open(REVOCATION_DB, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Failed to load revoked licenses: {e}")
        return {}


def save_revoked_licenses(revoked_licenses):
    """Save revoked licenses to JSON file"""
    try:
        REVOCATION_DB.parent.mkdir(parents=True, exist_ok=True)
        with open(REVOCATION_DB, 'w') as f:
            json.dump(revoked_licenses, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save revoked licenses: {e}")


@app.route('/api/license/check_revoked', methods=['POST'])
def check_revoked():
    """
    Check if a license is revoked
    
    Request JSON:
    {
        "license_id": "uuid-string",
        "device_id": "sha256-hash"
    }
    
    Response JSON:
    {
        "valid": true/false,
        "reason": "..." (if revoked)
    }
    """
    try:
        data = request.get_json()
        license_id = data.get('license_id')
        device_id = data.get('device_id')
        
        if not license_id:
            return jsonify({'error': 'Missing license_id'}), 400
        
        # Load revoked licenses
        revoked = load_revoked_licenses()
        
        # Check if revoked
        if license_id in revoked:
            revocation_info = revoked[license_id]
            logger.info(f"License check: {license_id[:8]}... - REVOKED")
            
            return jsonify({
                'valid': False,
                'reason': revocation_info.get('reason', 'License revoked'),
                'revoked_date': revocation_info.get('revoked_date'),
                'revoked_by': revocation_info.get('revoked_by', 'admin')
            })
        else:
            logger.info(f"License check: {license_id[:8]}... - VALID")
            
            return jsonify({
                'valid': True,
                'message': 'License is active'
            })
            
    except Exception as e:
        logger.error(f"Check revoked error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/license/revoke', methods=['POST'])
def revoke_license():
    """
    Revoke a license (admin only)
    
    Request JSON:
    {
        "license_id": "uuid-string",
        "reason": "Violation of terms",
        "admin_key": "your-admin-key"
    }
    
    Response JSON:
    {
        "success": true/false,
        "message": "..."
    }
    """
    try:
        data = request.get_json()
        license_id = data.get('license_id')
        reason = data.get('reason', 'No reason provided')
        admin_key = data.get('admin_key')
        
        # Validate admin key
        if admin_key != ADMIN_KEY:
            logger.warning(f"Unauthorized revoke attempt for {license_id}")
            return jsonify({'error': 'Unauthorized'}), 401
        
        if not license_id:
            return jsonify({'error': 'Missing license_id'}), 400
        
        # Load revoked licenses
        revoked = load_revoked_licenses()
        
        # Add to revocation list
        revoked[license_id] = {
            'revoked_date': datetime.now().isoformat(),
            'reason': reason,
            'revoked_by': 'admin'
        }
        
        # Save
        save_revoked_licenses(revoked)
        
        logger.info(f"License revoked: {license_id} - Reason: {reason}")
        
        return jsonify({
            'success': True,
            'message': f'License {license_id} revoked successfully'
        })
        
    except Exception as e:
        logger.error(f"Revoke error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/license/unrevoke', methods=['POST'])
def unrevoke_license():
    """
    Remove a license from revocation list (admin only)
    
    Request JSON:
    {
        "license_id": "uuid-string",
        "admin_key": "your-admin-key"
    }
    """
    try:
        data = request.get_json()
        license_id = data.get('license_id')
        admin_key = data.get('admin_key')
        
        # Validate admin key
        if admin_key != ADMIN_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
        
        if not license_id:
            return jsonify({'error': 'Missing license_id'}), 400
        
        # Load revoked licenses
        revoked = load_revoked_licenses()
        
        # Remove from revocation list
        if license_id in revoked:
            del revoked[license_id]
            save_revoked_licenses(revoked)
            
            logger.info(f"License unrevoked: {license_id}")
            
            return jsonify({
                'success': True,
                'message': f'License {license_id} removed from revocation list'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'License not found in revocation list'
            })
            
    except Exception as e:
        logger.error(f"Unrevoke error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/license/list_revoked', methods=['GET'])
def list_revoked():
    """
    List all revoked licenses (admin only)
    
    Query parameters:
        admin_key: Admin authentication key
    
    Response JSON:
    {
        "revoked_licenses": {
            "license_id_1": {...},
            "license_id_2": {...}
        }
    }
    """
    try:
        admin_key = request.args.get('admin_key')
        
        # Validate admin key
        if admin_key != ADMIN_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Load and return revoked licenses
        revoked = load_revoked_licenses()
        
        return jsonify({
            'revoked_licenses': revoked,
            'total_count': len(revoked)
        })
        
    except Exception as e:
        logger.error(f"List revoked error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'License Revocation Server',
        'version': '1.0.0'
    })


@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'service': 'ArtNet Controller - License Revocation Server',
        'version': '1.0.0',
        'endpoints': {
            'check_revoked': 'POST /api/license/check_revoked',
            'revoke': 'POST /api/license/revoke (admin)',
            'unrevoke': 'POST /api/license/unrevoke (admin)',
            'list_revoked': 'GET /api/license/list_revoked?admin_key=... (admin)',
            'health': 'GET /api/health'
        }
    })


if __name__ == '__main__':
    logger.info("="*60)
    logger.info("License Revocation Server Starting...")
    logger.info("="*60)
    logger.info(f"Revocation database: {REVOCATION_DB}")
    logger.info("")
    logger.info("⚠️  WARNING: Change ADMIN_KEY before production!")
    logger.info("")
    logger.info("Endpoints:")
    logger.info("  - POST /api/license/check_revoked (public)")
    logger.info("  - POST /api/license/revoke (admin)")
    logger.info("  - POST /api/license/unrevoke (admin)")
    logger.info("  - GET  /api/license/list_revoked (admin)")
    logger.info("="*60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
