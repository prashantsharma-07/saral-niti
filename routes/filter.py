from flask import Blueprint, jsonify, request
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import re

load_dotenv()

filter_bp = Blueprint("filter", __name__)

MONGO_URI = os.getenv("MONGO_URI")
if MONGO_URI:
    client = MongoClient(MONGO_URI)
else:
    client = None
db = client["saral_niti_db"] if client else None
schemes_collection = db["schemes"] if db is not None else None

def scheme_to_dict(scheme):
    scheme["_id"] = str(scheme["_id"])
    return scheme

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

# Allowed categories - matches scheme categories plus rural area
ALLOWED_CATEGORIES = [
    "agriculture", "health", "education", "housing", "employment",
    "women", "financial", "elderly", "youth", "disability", "rural", "rural area"
]

# GET /api/filter?category=health
@filter_bp.route("/api/filter", methods=["GET"])
def filter_schemes():
    try:
        category = request.args.get("category", "").strip().lower()
        tag = request.args.get("tag", "").strip()

        # ── INPUT VALIDATION ──
        # 1. Length check
        if len(category) > 50 or len(tag) > 50:
            return jsonify({"error": "Query value too long"}), 400

        # 2. Empty category and empty tag - return empty result
        if not category and not tag:
            return jsonify({
                "status": "ok",
                "category": "",
                "tag": "",
                "count": 0,
                "schemes": []
            })

        # 3. Whitelist check - only allow known categories if category is specified
        if category and category != "all" and category not in ALLOWED_CATEGORIES:
            return jsonify({"error": f"Invalid category: {category}"}), 400

        age_param = request.args.get("age", "").strip()
        target_age = None
        if age_param:
            try:
                val = int(age_param)
                if 0 <= val <= 120:
                    target_age = val
            except ValueError:
                pass

        and_clauses = []
        if category and category != "all":
            if category in ["rural", "rural area", "rural_area"]:
                and_clauses.append({
                    "$or": [
                        {"category": {"$regex": r"^rural", "$options": "i"}},
                        {"tags": {"$regex": r"rural\s*area|rural", "$options": "i"}},
                        {"tags_hi": {"$regex": r"ग्रामीण\s*क्षेत्र|ग्रामीण", "$options": "i"}}
                    ]
                })
            else:
                safe_category = re.escape(category)
                and_clauses.append({"category": {"$regex": f"^{safe_category}$", "$options": "i"}})

        if tag:
            safe_tag = re.escape(tag)
            and_clauses.append({
                "$or": [
                    {"tags": {"$regex": safe_tag, "$options": "i"}},
                    {"tags_hi": {"$regex": safe_tag, "$options": "i"}}
                ]
            })

        if target_age is not None:
            age_filter = {
                "$and": [
                    {
                        "$or": [
                            {"eligibility.min_age": None},
                            {"eligibility.min_age": {"$exists": False}},
                            {"eligibility.min_age": {"$lte": target_age}}
                        ]
                    },
                    {
                        "$or": [
                            {"eligibility.max_age": None},
                            {"eligibility.max_age": {"$exists": False}},
                            {"eligibility.max_age": {"$gte": target_age}}
                        ]
                    }
                ]
            }
            and_clauses.append(age_filter)

        filter = {"$and": and_clauses} if len(and_clauses) > 1 else (and_clauses[0] if and_clauses else {})

        results = []
        if schemes_collection is not None:
            try:
                results = list(schemes_collection.find(filter).limit(50))
                results = [scheme_to_dict(s) for s in results]
            except Exception:
                results = []

        if not results:
            # Fallback to local schemes.json
            offline_schemes = load_schemes_from_json()
            for s in offline_schemes:
                # Age filter check
                if target_age is not None:
                    elig = s.get("eligibility") or {}
                    min_age = elig.get("min_age")
                    max_age = elig.get("max_age")
                    if min_age is not None and min_age > target_age:
                        continue
                    if max_age is not None and max_age < target_age:
                        continue

                # Category / tag check
                if category and category != "all":
                    if category in ["rural", "rural area", "rural_area"]:
                        s_tags = [t.lower() for t in (s.get("tags") or [])]
                        s_tags_hi = [t for t in (s.get("tags_hi") or [])]
                        is_match = (
                            s.get("category", "").lower() == "rural"
                            or any("rural" in t for t in s_tags)
                            or any("ग्रामीण" in t for t in s_tags_hi)
                        )
                        if not is_match:
                            continue
                    elif s.get("category", "").lower() != category:
                        continue

                if tag:
                    s_tags = [t.lower() for t in (s.get("tags") or [])]
                    s_tags_hi = [t.lower() for t in (s.get("tags_hi") or [])]
                    if not any(tag.lower() in t for t in s_tags) and not any(tag.lower() in t for t in s_tags_hi):
                        continue

                results.append(scheme_to_dict(s))
                if len(results) >= 50:
                    break

        return jsonify({
            "status": "ok",
            "category": category,
            "tag": tag,
            "age": target_age,
            "count": len(results),
            "schemes": results
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500