# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
P21 — Platform Publishers
Each function posts content to a specific social platform via its API.
All return {"post_id": ..., "url": ...} on success, raise on failure.
"""
import frappe
import requests
import json


def _get_settings():
    return frappe.get_cached_doc("AuraCRM Settings")


# ---------------------------------------------------------------------------
# Facebook (Meta Graph API)
# ---------------------------------------------------------------------------
def publish_facebook(item):
    """Post to Facebook Page using Graph API."""
    settings = _get_settings()
    token = settings.get("meta_page_access_token") or settings.get("meta_access_token")
    page_id = settings.get("facebook_page_id")
    if not token or not page_id:
        raise ValueError("Facebook Page token or Page ID not configured")

    url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
    payload = {"message": item.content_body, "access_token": token}

    if item.media_url:
        url = f"https://graph.facebook.com/v18.0/{page_id}/photos"
        payload["url"] = item.media_url

    resp = requests.post(url, data=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    post_id = data.get("id") or data.get("post_id", "")
    return {"post_id": post_id, "url": f"https://facebook.com/{post_id}"}


# ---------------------------------------------------------------------------
# Instagram (Meta Graph API — Business Account)
# ---------------------------------------------------------------------------
def publish_instagram(item):
    """Post to Instagram Business Account (requires media_url)."""
    settings = _get_settings()
    token = settings.get("meta_access_token")
    ig_account_id = settings.get("instagram_business_account_id")
    if not token or not ig_account_id:
        raise ValueError("Instagram Business Account not configured")

    if not item.media_url:
        raise ValueError("Instagram requires a media_url")

    # Step 1: Create media container
    container_url = f"https://graph.facebook.com/v18.0/{ig_account_id}/media"
    container_payload = {
        "image_url": item.media_url,
        "caption": item.content_body or "",
        "access_token": token,
    }
    resp = requests.post(container_url, data=container_payload, timeout=30)
    resp.raise_for_status()
    container_id = resp.json().get("id")

    # Step 2: Publish the container
    publish_url = f"https://graph.facebook.com/v18.0/{ig_account_id}/media_publish"
    resp2 = requests.post(
        publish_url,
        data={"creation_id": container_id, "access_token": token},
        timeout=30,
    )
    resp2.raise_for_status()
    post_id = resp2.json().get("id", "")
    return {"post_id": post_id, "url": f"https://instagram.com/p/{post_id}"}


# ---------------------------------------------------------------------------
# Twitter / X (v2 API)
# ---------------------------------------------------------------------------
def publish_twitter(item):
    """Post a tweet using Twitter API v2 with OAuth2 Bearer."""
    settings = _get_settings()
    bearer = settings.get("twitter_bearer_token")
    if not bearer:
        raise ValueError("Twitter bearer token not configured")

    url = "https://api.twitter.com/2/tweets"
    headers = {
        "Authorization": f"Bearer {bearer}",
        "Content-Type": "application/json",
    }
    payload = {"text": item.content_body[:280]}

    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json().get("data", {})
    tweet_id = data.get("id", "")
    return {"post_id": tweet_id, "url": f"https://twitter.com/i/web/status/{tweet_id}"}


# ---------------------------------------------------------------------------
# LinkedIn (v2 API — UGC Posts)
# ---------------------------------------------------------------------------
def publish_linkedin(item):
    """Post to LinkedIn Company Page."""
    settings = _get_settings()
    token = settings.get("linkedin_access_token")
    org_id = settings.get("linkedin_organization_id")
    if not token or not org_id:
        raise ValueError("LinkedIn access token or Organization ID not configured")

    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    payload = {
        "author": f"urn:li:organization:{org_id}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": item.content_body},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
    resp.raise_for_status()
    post_id = resp.headers.get("x-restli-id", resp.json().get("id", ""))
    return {"post_id": post_id, "url": f"https://linkedin.com/feed/update/{post_id}"}


# ---------------------------------------------------------------------------
# TikTok (Content Posting API)
# ---------------------------------------------------------------------------
def publish_tiktok(item):
    """Placeholder — TikTok Content Posting API requires video upload.
    For now, log and return a stub; full implementation needs video workflow."""
    settings = _get_settings()
    token = settings.get("tiktok_access_token")
    if not token:
        raise ValueError("TikTok access token not configured")

    frappe.log_error(
        title="TikTok publish stub",
        message=f"TikTok publishing not yet implemented for queue item: {item.name}",
    )
    return {"post_id": "stub", "url": ""}
