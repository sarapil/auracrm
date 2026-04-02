"""
P28 — Review Aggregator
Pulls reviews from external platforms (Google, Facebook, etc.)
and creates Review Entry documents for unified management.
"""
import frappe
from frappe.utils import now_datetime
import requests


# ---------------------------------------------------------------------------
# Scheduled: Pull reviews from configured platforms
# ---------------------------------------------------------------------------
def pull_external_reviews():
    """Scheduled daily — pull new reviews from all configured platforms."""
    settings = frappe.get_cached_doc("AuraCRM Settings")

    pulled = 0

    if settings.get("google_place_id"):
        pulled += _pull_google_reviews(settings)

    if settings.get("facebook_page_id") and settings.get("meta_page_access_token"):
        pulled += _pull_facebook_reviews(settings)

    if pulled:
        frappe.db.commit()

    return pulled


# ---------------------------------------------------------------------------
# Google Reviews (Places API)
# ---------------------------------------------------------------------------
def _pull_google_reviews(settings):
    """Pull reviews from Google Places API."""
    api_key = settings.get("google_places_api_key") or settings.get("google_cse_api_key")
    place_id = settings.get("google_place_id")

    if not api_key or not place_id:
        return 0

    try:
        resp = requests.get(
            "https://maps.googleapis.com/maps/api/place/details/json",
            params={
                "place_id": place_id,
                "fields": "reviews",
                "key": api_key,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        reviews = data.get("result", {}).get("reviews", [])
        count = 0

        for review in reviews:
            author_name = review.get("author_name", "")
            rating = review.get("rating", 0)
            text = review.get("text", "")
            time_val = review.get("time", 0)
            review_id = f"google_{place_id}_{time_val}_{author_name[:10]}"

            if frappe.db.exists("Review Entry", {"platform_review_id": review_id}):
                continue

            _create_review_entry(
                platform="Google",
                reviewer_name=author_name,
                rating=rating,
                review_text=text,
                platform_review_id=review_id,
                reviewer_profile_url=review.get("author_url", ""),
            )
            count += 1

        return count
    except Exception as e:
        frappe.log_error(title="Google reviews pull failed", message=str(e))
        return 0


# ---------------------------------------------------------------------------
# Facebook Reviews (Graph API)
# ---------------------------------------------------------------------------
def _pull_facebook_reviews(settings):
    """Pull reviews/recommendations from Facebook Page."""
    token = settings.get("meta_page_access_token") or settings.get("meta_access_token")
    page_id = settings.get("facebook_page_id")

    if not token or not page_id:
        return 0

    try:
        resp = requests.get(
            f"https://graph.facebook.com/v18.0/{page_id}/ratings",
            params={"access_token": token, "limit": 25},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        reviews = data.get("data", [])
        count = 0

        for review in reviews:
            reviewer = review.get("reviewer", {})
            reviewer_name = reviewer.get("name", "Anonymous")
            rating = review.get("rating") or (5 if review.get("recommendation_type") == "positive" else 2)
            text = review.get("review_text", "")
            review_id = review.get("open_graph_story", {}).get("id", "")

            if not review_id:
                review_id = f"fb_{page_id}_{reviewer_name[:10]}_{review.get('created_time', '')[:10]}"

            if frappe.db.exists("Review Entry", {"platform_review_id": review_id}):
                continue

            _create_review_entry(
                platform="Facebook",
                reviewer_name=reviewer_name,
                rating=rating,
                review_text=text,
                platform_review_id=review_id,
            )
            count += 1

        return count
    except Exception as e:
        frappe.log_error(title="Facebook reviews pull failed", message=str(e))
        return 0


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------
@frappe.whitelist()
def get_reputation_summary():
    """Return aggregate reputation metrics."""
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    total = frappe.db.count("Review Entry")
    if not total:
        return {
            "total_reviews": 0,
            "average_rating": 0,
            "rating_distribution": {},
            "platforms": {},
        }

    avg_rating = frappe.db.sql(
        "SELECT AVG(rating) FROM `tabReview Entry`"
    )[0][0] or 0

    # Distribution by rating
    distribution = {}
    for i in range(1, 6):
        distribution[i] = frappe.db.count("Review Entry", {"rating": i})

    # By platform
    platforms = {}
    platform_data = frappe.db.sql(
        """SELECT platform, COUNT(*) as cnt, AVG(rating) as avg_r
        FROM `tabReview Entry`
        GROUP BY platform""",
        as_dict=True,
    )
    for p in platform_data:
        platforms[p.platform] = {
            "count": p.cnt,
            "average_rating": round(p.avg_r, 2),
        }

    # Sentiment breakdown
    flagged_count = frappe.db.count("Review Entry", {"flagged": 1})
    responded_count = frappe.db.count("Review Entry", {"response_status": ("in", ["Approved", "Published"])})

    return {
        "total_reviews": total,
        "average_rating": round(avg_rating, 2),
        "rating_distribution": distribution,
        "platforms": platforms,
        "flagged_count": flagged_count,
        "responded_count": responded_count,
        "response_rate": round((responded_count / max(flagged_count, 1)) * 100, 1),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _create_review_entry(platform, reviewer_name, rating, review_text,
                         platform_review_id="", reviewer_profile_url=""):
    """Create a Review Entry document."""
    entry = frappe.new_doc("Review Entry")
    entry.platform = platform
    entry.reviewer_name = reviewer_name
    entry.rating = rating
    entry.review_text = review_text
    entry.platform_review_id = platform_review_id
    entry.reviewer_profile_url = reviewer_profile_url
    entry.captured_at = now_datetime()
    entry.flagged = 1 if rating <= 2 else 0
    entry.insert(ignore_permissions=True)
    return entry.name
