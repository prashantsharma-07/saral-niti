from flask import Blueprint, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
from bson import ObjectId
import os

load_dotenv()

schemes_bp = Blueprint("schemes", __name__)

MONGO_URI = os.getenv("MONGO_URI")
if MONGO_URI:
    client = MongoClient(MONGO_URI)
    db = client["saral_niti_db"]
    schemes_collection = db["schemes"]
else:
    client = None
    db = None
    schemes_collection = None

import json

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "schemes.json")

def load_schemes_from_json():
    """Fallback in case MongoDB is offline."""
    if os.path.exists(DATA_PATH):
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                for idx, item in enumerate(data):
                    if "_id" not in item:
                        item["_id"] = f"local_{idx}"
                return data
        except Exception:
            return []
    return []

def scheme_to_dict(scheme):
    if "_id" in scheme:
        scheme["_id"] = str(scheme["_id"])
    return scheme

# GET /api/schemes — get all schemes
@schemes_bp.route("/api/schemes", methods=["GET"])
def get_all_schemes():
    try:
        schemes = []
        if schemes_collection is not None:
            try:
                schemes = list(schemes_collection.find())
                schemes = [scheme_to_dict(s) for s in schemes]
            except Exception:
                schemes = []

        if not schemes:
            schemes = [scheme_to_dict(s) for s in load_schemes_from_json()]

        return jsonify({
            "status": "ok",
            "count": len(schemes),
            "schemes": schemes
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# GET /api/schemes/<id> — get one scheme by ID
@schemes_bp.route("/api/schemes/<id>", methods=["GET"])
def get_scheme_by_id(id):
    try:
        scheme = None
        if schemes_collection is not None:
            try:
                scheme = schemes_collection.find_one({"_id": ObjectId(id)})
            except Exception:
                scheme = None

        if not scheme:
            offline = load_schemes_from_json()
            for s in offline:
                if str(s.get("_id")) == str(id) or s.get("slug") == str(id):
                    scheme = s
                    break

        if not scheme:
            return jsonify({"error": "Scheme not found"}), 404
        return jsonify(scheme_to_dict(scheme))
    except Exception as e:
        return jsonify({"error": str(e)}), 500