from datetime import datetime

def create_scheme(
    title, slug, description, category,
    tags, eligibility, benefits,
    application_url, ministry,
    launched_year, is_active=True
):
    return {
        "title": title,
        "slug": slug,
        "description": description,
        "category": category,
        "tags": tags,
        "eligibility": {
            "min_age": eligibility.get("min_age"),
            "max_age": eligibility.get("max_age"),
            "gender": eligibility.get("gender", "all"),
            "income_limit": eligibility.get("income_limit"),
            "caste": eligibility.get("caste", ["general","obc","sc","st"]),
            "occupation": eligibility.get("occupation", []),
            "state": eligibility.get("state", "all"),
            "area": eligibility.get("area", "all")
        },
        "benefits": benefits,
        "application_url": application_url,
        "ministry": ministry,
        "launched_year": launched_year,
        "is_active": is_active,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }