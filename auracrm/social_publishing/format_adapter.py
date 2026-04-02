"""
P21 — Format Adapter
Transforms a generic content body into platform-specific formats
(character limits, hashtag positioning, mention styles, etc.).
"""
import re


# Platform constraints
PLATFORM_LIMITS = {
    "Facebook": {"chars": 63206, "hashtags_max": 30},
    "Instagram": {"chars": 2200, "hashtags_max": 30},
    "Twitter": {"chars": 280, "hashtags_max": 5},
    "LinkedIn": {"chars": 3000, "hashtags_max": 10},
    "TikTok": {"chars": 2200, "hashtags_max": 15},
}


def adapt_content(content_body, platform, hashtags=None, cta_link=None):
    """Return platform-adapted version of content_body.

    Args:
        content_body: Raw content text.
        platform: One of Facebook, Instagram, Twitter, LinkedIn, TikTok.
        hashtags: Optional list of hashtag strings (without #).
        cta_link: Optional call-to-action URL.

    Returns:
        str: Adapted content ready to post.
    """
    limits = PLATFORM_LIMITS.get(platform, {"chars": 2000, "hashtags_max": 10})
    text = content_body or ""

    # Add CTA link
    if cta_link:
        text = _append_cta(text, cta_link, platform)

    # Add hashtags
    if hashtags:
        text = _add_hashtags(text, hashtags, platform, limits["hashtags_max"])

    # Truncate to platform limit
    max_chars = limits["chars"]
    if len(text) > max_chars:
        text = text[: max_chars - 3] + "..."

    # Platform-specific formatting
    text = _platform_format(text, platform)

    return text


def _append_cta(text, cta_link, platform):
    """Append CTA link with platform conventions."""
    if platform == "Instagram":
        # Instagram doesn't support clickable links in captions
        return f"{text}\n\n🔗 Link in bio"
    elif platform == "Twitter":
        # Twitter shortens URLs to 23 chars
        return f"{text}\n{cta_link}"
    else:
        return f"{text}\n\n👉 {cta_link}"


def _add_hashtags(text, hashtags, platform, max_count):
    """Add hashtags to text respecting platform conventions."""
    tags = [f"#{h.strip().replace(' ', '')}" for h in hashtags[:max_count]]
    tag_str = " ".join(tags)

    if platform == "Instagram":
        # Instagram: hashtags at the end, separated by dots
        return f"{text}\n.\n.\n.\n{tag_str}"
    elif platform == "Twitter":
        # Twitter: inline hashtags are better
        return f"{text}\n{tag_str}"
    else:
        return f"{text}\n\n{tag_str}"


def _platform_format(text, platform):
    """Apply platform-specific text formatting rules."""
    if platform == "LinkedIn":
        # LinkedIn: Add line breaks for readability
        text = re.sub(r"\n{3,}", "\n\n", text)
    elif platform == "Twitter":
        # Twitter: Use thread notation if > 280 chars (handled at scheduler level)
        pass

    return text.strip()


def estimate_engagement_score(content_body, platform):
    """Heuristic engagement score (0-100) based on content characteristics."""
    score = 50
    text = content_body or ""

    # Emoji presence (slight boost)
    emoji_count = len(re.findall(r"[\U0001f300-\U0001f9ff]", text))
    score += min(emoji_count * 2, 10)

    # Hashtag count
    hashtag_count = len(re.findall(r"#\w+", text))
    if platform == "Instagram" and 5 <= hashtag_count <= 20:
        score += 10
    elif platform == "Twitter" and 1 <= hashtag_count <= 3:
        score += 10

    # Question marks (engagement driver)
    if "?" in text:
        score += 5

    # CTA keywords
    cta_words = ["link", "click", "sign up", "register", "buy", "shop", "visit"]
    if any(w in text.lower() for w in cta_words):
        score += 5

    # Length optimization
    length = len(text)
    if platform == "Twitter" and 100 <= length <= 240:
        score += 10
    elif platform == "LinkedIn" and 150 <= length <= 1200:
        score += 10
    elif platform == "Instagram" and 100 <= length <= 600:
        score += 10

    return min(score, 100)
