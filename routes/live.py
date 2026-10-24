# backend/routes/live.py
# Live API integration with MyScheme Gov API

import requests
from flask import Blueprint, jsonify, request

live_bp = Blueprint('live', __name__)

MYSCHEME_API_BASE = "https://api.myscheme.gov.in/search/v4/schemes"

@live_bp.route('/api/live/schemes', methods=['GET'])
def get_live_schemes():
    """Fetch live schemes from MyScheme API"""
    try:
        keyword = request.args.get('q', '')
        params = {
            'keyword': keyword,
            'lang': 'en',
            'pageSize': 10,
            'pageNo': 1
        }
        response = requests.get(MYSCHEME_API_BASE, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return jsonify({
            "source": "myscheme_live",
            "data": data
        }), 200

    except requests.exceptions.Timeout:
        return jsonify({"error": "MyScheme API timed out"}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 502


@live_bp.route('/api/live/scheme/<scheme_id>', methods=['GET'])
def get_live_scheme_by_id(scheme_id):
    """Fetch a single scheme by ID from MyScheme API"""
    try:
        url = f"{MYSCHEME_API_BASE}/{scheme_id}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return jsonify(response.json()), 200

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 502