from flask import Blueprint, jsonify, request
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import re
import json

load_dotenv()

search_bp = Blueprint("search", __name__)
MONGO_URI = os.getenv("MONGO_URI")
if MONGO_URI:
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    except Exception:
        client = None
else:
    client = None

db = client["saral_niti_db"] if client is not None else None
schemes_collection = db["schemes"] if db is not None else None

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "schemes.json")

def scheme_to_dict(scheme):
    if "_id" in scheme:
        scheme["_id"] = str(scheme["_id"])
    return scheme

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

def extract_age_and_text(raw_query, raw_age):
    """
    Extracts age and remaining text query from user input.
    Examples:
      - raw_query="25" -> age=25, text=""
      - raw_query="age 25" -> age=25, text=""
      - raw_query="farmer 25 years" -> age=25, text="farmer"
      - raw_query="scholarship 18" -> age=18, text="scholarship"
      - raw_query="farmer", raw_age="30" -> age=30, text="farmer"
    """
    target_age = None
    text_query = (raw_query or "").strip()

    # 1. Explicit age parameter provided
    if raw_age:
        try:
            val = int(raw_age)
            if 0 <= val <= 120:
                target_age = val
        except ValueError:
            pass

    # 2. If no target_age yet, check in query text
    if target_age is None and text_query:
        # A. Query is just a number (e.g. "25")
        if text_query.isdigit():
            val = int(text_query)
            if 0 <= val <= 120:
                target_age = val
                text_query = ""
        else:
            # B. Query contains explicit age keyword, e.g. "age 25", "25 years old", "25 yrs", "25 saal", "25 varsh"
            pattern_explicit = r'(?i)\b(?:age[:\s=]+(\d{1,3})|(\d{1,3})\s*(?:years?(?:\s*old)?|yrs?|yr|saal|varsh|साल|वर्ष))\b'
            match = re.search(pattern_explicit, text_query)
            if match:
                num_str = match.group(1) or match.group(2)
                val = int(num_str)
                if 0 <= val <= 120:
                    target_age = val
                    text_query = re.sub(pattern_explicit, '', text_query).strip()
            else:
                # C. Query contains a number like "farmer 25" or "25 farmer" (excluding ordinals like 10th, 12th)
                pattern_num = r'(?i)\b(?<!\d)(\d{1,2})(?!\s*(?:th|st|nd|rd|%|lakh|crore|k|rs|rupees?))\b'
                match_num = re.search(pattern_num, text_query)
                if match_num:
                    val = int(match_num.group(1))
                    if 0 <= val <= 110:
                        target_age = val
                        text_query = (text_query[:match_num.start()] + text_query[match_num.end():]).strip()
                        text_query = re.sub(r'\s+', ' ', text_query).strip()

    return target_age, text_query

def filter_schemes_offline(text_query, target_age):
    """Filters local JSON schemes when MongoDB is unavailable."""
    schemes = load_schemes_from_json()
    results = []
    text_lower = text_query.lower() if text_query else ""

    for s in schemes:
        # Check age suitability
        if target_age is not None:
            elig = s.get("eligibility") or {}
            min_age = elig.get("min_age")
            max_age = elig.get("max_age")
            if min_age is not None and min_age > target_age:
                continue
            if max_age is not None and max_age < target_age:
                continue

        # Check text match
        if text_lower:
            title = (s.get("title") or "").lower()
            title_hi = (s.get("title_hi") or "").lower()
            desc = (s.get("description") or "").lower()
            desc_hi = (s.get("description_hi") or "").lower()
            tags = " ".join(s.get("tags") or []).lower()
            tags_hi = " ".join(s.get("tags_hi") or []).lower()
            minis = (s.get("ministry") or "").lower()
            minis_hi = (s.get("ministry_hi") or "").lower()

            if not any(text_lower in field for field in [title, title_hi, desc, desc_hi, tags, tags_hi, minis, minis_hi]):
                continue

        results.append(scheme_to_dict(s))
    return results[:50]

# GET /api/search?q=keyword&age=25
@search_bp.route("/api/search", methods=["GET"])
def search_schemes():
    try:
        raw_query = request.args.get("q", "").strip()
        raw_age = request.args.get("age", "").strip()

        # ── INPUT VALIDATION ──
        if len(raw_query) > 100:
            return jsonify({"error": "Search query too long (max 100 characters)"}), 400

        # Extract target age and clean text
        target_age, text_query = extract_age_and_text(raw_query, raw_age)

        # Empty query and no age: return empty result
        if not text_query and target_age is None:
            return jsonify({
                "status": "ok",
                "query": "",
                "age": None,
                "count": 0,
                "schemes": []
            })

        # Try MongoDB first
        results = None
        if schemes_collection is not None:
            try:
                and_clauses = []

                # 1. Text filter
                if text_query:
                    safe_query = re.escape(text_query)
                    text_filter = {
                        "$or": [
                            {"title": {"$regex": safe_query, "$options": "i"}},
                            {"title_hi": {"$regex": safe_query, "$options": "i"}},
                            {"description": {"$regex": safe_query, "$options": "i"}},
                            {"description_hi": {"$regex": safe_query, "$options": "i"}},
                            {"tags": {"$regex": safe_query, "$options": "i"}},
                            {"tags_hi": {"$regex": safe_query, "$options": "i"}},
                            {"ministry": {"$regex": safe_query, "$options": "i"}},
                            {"ministry_hi": {"$regex": safe_query, "$options": "i"}}
                        ]
                    }
                    and_clauses.append(text_filter)

                # 2. Age eligibility filter
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

                mongo_filter = {"$and": and_clauses} if len(and_clauses) > 1 else and_clauses[0]
                db_results = list(schemes_collection.find(mongo_filter).limit(50))
                results = [scheme_to_dict(s) for s in db_results]
            except Exception:
                results = None

        # Fallback to JSON if MongoDB was not available or errored
        if results is None:
            results = filter_schemes_offline(text_query, target_age)

        return jsonify({
            "status": "ok",
            "query": raw_query,
            "text_query": text_query,
            "age": target_age,
            "count": len(results),
            "schemes": results
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500