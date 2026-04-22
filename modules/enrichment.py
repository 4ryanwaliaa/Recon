"""
╔══════════════════════════════════════════════════════════════╗
║  Profile Enrichment Engine                                  ║
║  Fetches bio, followers, profile pic from found profiles    ║
║  Supports: Instagram, GitHub, Reddit, Gravatar, and more    ║
╚══════════════════════════════════════════════════════════════╝
"""

import re
import requests
import time
import hashlib
from typing import Optional

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
TIMEOUT = 8


# ──────────────────────────────────────────────────────────────
#  Image Downloader
# ──────────────────────────────────────────────────────────────

def _download_image(url: str, timeout: int = 6) -> bytes:
    """Download an image and return raw bytes."""
    if not url or not url.startswith("http"):
        return b""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, stream=True)
        if resp.status_code == 200 and len(resp.content) < 5_000_000:
            return resp.content
    except Exception:
        pass
    return b""


# ──────────────────────────────────────────────────────────────
#  Instagram Enrichment (3 methods with fallbacks)
# ──────────────────────────────────────────────────────────────

def _enrich_instagram(username: str) -> dict:
    """
    Method 1: Session-based API (cookies from homepage)
    Method 2: Direct API endpoint
    Method 3: Full HTML scraping with robust meta parser
    Method 4: Instaloader library
    """
    data = {"platform": "Instagram", "username": username}

    # Method 1: Session-based — visit homepage first for cookies, then API
    try:
        s = requests.Session()
        s.headers.update({
            "User-Agent": HEADERS["User-Agent"],
            "Accept-Language": "en-US,en;q=0.9",
        })
        # Visit homepage to get cookies (csrftoken, mid, ig_did, etc.)
        s.get("https://www.instagram.com/", timeout=8)
        import time as _t; _t.sleep(0.5)

        csrf = s.cookies.get("csrftoken", "")
        s.headers.update({
            "X-CSRFToken": csrf,
            "X-IG-App-ID": "936619743392459",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"https://www.instagram.com/{username}/",
            "Accept": "*/*",
        })
        r = s.get(
            f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}",
            timeout=TIMEOUT,
        )
        if r.status_code == 200:
            j = r.json()
            user = j.get("data", {}).get("user", {})
            if not user:
                user = j.get("graphql", {}).get("user", j.get("user", {}))
            if user:
                data["bio"] = user.get("biography", "") or ""
                data["display_name"] = user.get("full_name", "") or ""
                data["followers"] = user.get("edge_followed_by", {}).get("count", 0)
                data["following"] = user.get("edge_follow", {}).get("count", 0)
                data["posts"] = user.get("edge_owner_to_timeline_media", {}).get("count", 0)
                data["profile_pic_url"] = user.get("profile_pic_url_hd", user.get("profile_pic_url", ""))
                data["is_private"] = user.get("is_private", False)
                data["is_verified"] = user.get("is_verified", False)
                if data.get("profile_pic_url"):
                    data["profile_pic_data"] = _download_image(data["profile_pic_url"])
                if data.get("bio") or data.get("profile_pic_url"):
                    return data
    except Exception:
        pass

    # Method 2: Direct API endpoint (no session)
    try:
        url = f"https://www.instagram.com/{username}/?__a=1&__d=dis"
        resp = requests.get(url, headers={
            **HEADERS,
            "Accept": "application/json",
            "X-IG-App-ID": "936619743392459",
        }, timeout=TIMEOUT)
        if resp.status_code == 200:
            j = resp.json()
            user = j.get("graphql", {}).get("user", {})
            if not user:
                user = j.get("user", {})
            if user:
                data["bio"] = user.get("biography", "") or ""
                data["display_name"] = user.get("full_name", "") or ""
                data["followers"] = user.get("edge_followed_by", {}).get("count", 0)
                data["profile_pic_url"] = user.get("profile_pic_url_hd", user.get("profile_pic_url", ""))
                data["is_private"] = user.get("is_private", False)
                data["is_verified"] = user.get("is_verified", False)
                if data.get("profile_pic_url"):
                    data["profile_pic_data"] = _download_image(data["profile_pic_url"])
                if data.get("bio") or data.get("profile_pic_url"):
                    return data
    except Exception:
        pass

    # Method 3: Full HTML scrape — parse meta tags from page
    try:
        page_url = f"https://www.instagram.com/{username}/"
        resp = requests.get(page_url, headers={
            **HEADERS,
            "Accept": "text/html,application/xhtml+xml",
        }, timeout=TIMEOUT)
        if resp.status_code == 200:
            html = resp.text
            # Use robust meta tag parser (same as _enrich_from_og_tags)
            meta_tags = re.findall(r'<meta\s+([^>]+?)/?>', html, re.IGNORECASE)
            meta_map = {}
            for tag_attrs in meta_tags:
                content_m = re.search(r'content\s*=\s*["\']([^"\']*)["\']', tag_attrs, re.IGNORECASE)
                if not content_m:
                    continue
                content = content_m.group(1)
                prop_m = re.search(r'(?:property|name)\s*=\s*["\']([^"\']*)["\']', tag_attrs, re.IGNORECASE)
                if not prop_m:
                    continue
                prop = prop_m.group(1).lower()
                if prop not in meta_map:
                    meta_map[prop] = content

            # Parse og:description for followers/bio
            desc = meta_map.get("og:description", "")
            if desc:
                followers_m = re.search(r'([\d,.]+[KMkm]?)\s+Follower', desc)
                following_m = re.search(r'([\d,.]+[KMkm]?)\s+Following', desc)
                posts_m = re.search(r'([\d,.]+[KMkm]?)\s+Post', desc)
                if followers_m:
                    data["followers"] = _parse_count(followers_m.group(1))
                if following_m:
                    data["following"] = _parse_count(following_m.group(1))
                if posts_m:
                    data["posts"] = _parse_count(posts_m.group(1))
                bio_m = re.search(r'Posts?\s*[-\u2013\u2014]\s*(.*)', desc)
                if bio_m:
                    data["bio"] = bio_m.group(1).strip().rstrip('"')

            # Profile pic from og:image (skip default IG logo)
            pic = meta_map.get("og:image", "")
            if pic and pic.startswith("http") and "instagram" not in pic.split("/")[2].replace("www.", "").replace("scontent", "skip"):
                # Only use if it's a CDN pic (scontent), not a generic IG logo
                pass
            if pic and "scontent" in pic:
                data["profile_pic_url"] = pic
                data["profile_pic_data"] = _download_image(pic)

            # Display name from og:title
            title = meta_map.get("og:title", "")
            if title:
                name_m = re.match(r'^(.*?)\s*[\(\[]?@', title)
                if name_m:
                    data["display_name"] = name_m.group(1).strip()

            # Also try embedded JSON (window._sharedData or window.__additionalDataLoaded)
            shared = re.search(r'window\._sharedData\s*=\s*(\{.+?\});</script>', html)
            if shared:
                import json
                try:
                    sd = json.loads(shared.group(1))
                    user = sd.get("entry_data", {}).get("ProfilePage", [{}])[0].get("graphql", {}).get("user", {})
                    if user:
                        data["bio"] = user.get("biography", "") or data.get("bio", "")
                        data["display_name"] = user.get("full_name", "") or data.get("display_name", "")
                        data["followers"] = user.get("edge_followed_by", {}).get("count", 0) or data.get("followers", 0)
                        pic_url = user.get("profile_pic_url_hd", user.get("profile_pic_url", ""))
                        if pic_url:
                            data["profile_pic_url"] = pic_url
                            data["profile_pic_data"] = _download_image(pic_url)
                        data["is_private"] = user.get("is_private", False)
                        data["is_verified"] = user.get("is_verified", False)
                except (json.JSONDecodeError, IndexError, KeyError):
                    pass

            if data.get("bio") or data.get("profile_pic_data") or data.get("followers"):
                return data
    except Exception:
        pass

    # Method 4: Instaloader fallback
    try:
        import instaloader
        L = instaloader.Instaloader()
        profile = instaloader.Profile.from_username(L.context, username)
        data["bio"] = profile.biography or ""
        data["display_name"] = profile.full_name or ""
        data["followers"] = profile.followers
        data["following"] = profile.followees
        data["posts"] = profile.mediacount
        data["profile_pic_url"] = profile.profile_pic_url or ""
        data["is_private"] = profile.is_private
        data["is_verified"] = profile.is_verified
        if data["profile_pic_url"]:
            data["profile_pic_data"] = _download_image(data["profile_pic_url"])
        return data
    except ImportError:
        pass
    except Exception:
        pass

    return data


def _parse_count(s: str) -> int:
    """Parse '1,234' or '1.2K' or '3.5M' to int."""
    s = s.replace(",", "").strip()
    try:
        if s[-1].upper() == "K":
            return int(float(s[:-1]) * 1000)
        elif s[-1].upper() == "M":
            return int(float(s[:-1]) * 1000000)
        return int(float(s))
    except (ValueError, IndexError):
        return 0


# ──────────────────────────────────────────────────────────────
#  GitHub Enrichment (free API, no key needed)
# ──────────────────────────────────────────────────────────────

def _enrich_github(username: str) -> dict:
    data = {"platform": "GitHub", "username": username}
    try:
        resp = requests.get(
            f"https://api.github.com/users/{username}",
            headers={"User-Agent": HEADERS["User-Agent"], "Accept": "application/vnd.github.v3+json"},
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            j = resp.json()
            data["bio"] = j.get("bio", "") or ""
            data["display_name"] = j.get("name", "") or ""
            data["followers"] = j.get("followers", 0)
            data["following"] = j.get("following", 0)
            data["repos"] = j.get("public_repos", 0)
            data["location"] = j.get("location", "") or ""
            data["company"] = j.get("company", "") or ""
            data["profile_pic_url"] = j.get("avatar_url", "")
            data["blog"] = j.get("blog", "") or ""
            data["created_at"] = j.get("created_at", "")
            if data["profile_pic_url"]:
                data["profile_pic_data"] = _download_image(data["profile_pic_url"])
    except Exception:
        pass
    return data


# ──────────────────────────────────────────────────────────────
#  Reddit Enrichment
# ──────────────────────────────────────────────────────────────

def _enrich_reddit(username: str) -> dict:
    data = {"platform": "Reddit", "username": username}
    try:
        resp = requests.get(
            f"https://www.reddit.com/user/{username}/about.json",
            headers=HEADERS, timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            j = resp.json().get("data", {})
            data["bio"] = j.get("subreddit", {}).get("public_description", "") or ""
            data["display_name"] = j.get("subreddit", {}).get("title", "") or ""
            data["followers"] = j.get("subreddit", {}).get("subscribers", 0)
            data["karma"] = j.get("total_karma", 0)
            data["profile_pic_url"] = j.get("icon_img", "").split("?")[0]
            data["created_at"] = str(j.get("created_utc", ""))
            if data["profile_pic_url"]:
                data["profile_pic_data"] = _download_image(data["profile_pic_url"])
    except Exception:
        pass
    return data


# ──────────────────────────────────────────────────────────────
#  Gravatar Enrichment (works for any user via hash)
# ──────────────────────────────────────────────────────────────

def _enrich_gravatar(username: str) -> dict:
    data = {"platform": "Gravatar", "username": username}
    try:
        # Gravatar uses email hash — try username as-is first
        profile_url = f"https://en.gravatar.com/{username}.json"
        resp = requests.get(profile_url, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 200:
            j = resp.json()
            entry = j.get("entry", [{}])[0]
            data["display_name"] = entry.get("displayName", "") or ""
            data["bio"] = entry.get("aboutMe", "") or ""
            data["profile_pic_url"] = entry.get("thumbnailUrl", "")
            if data["profile_pic_url"]:
                # Get high-res version
                data["profile_pic_url"] = data["profile_pic_url"].split("?")[0] + "?s=400"
                data["profile_pic_data"] = _download_image(data["profile_pic_url"])
    except Exception:
        pass
    return data


# ──────────────────────────────────────────────────────────────
#  Generic OG-tag scraper (fallback for any platform)
# ──────────────────────────────────────────────────────────────

def _enrich_from_og_tags(url: str) -> dict:
    """Extract bio and profile pic from OpenGraph/Twitter meta tags."""
    data = {}
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code != 200:
            return data

        html = resp.text  # scan full page — Pinterest puts OG tags 700KB+ deep

        # Step 1: Find ALL <meta ...> tags
        meta_tags = re.findall(r'<meta\s+([^>]+?)/?>', html, re.IGNORECASE)

        # Step 2: Parse each meta tag into a dict of attributes
        meta_map = {}  # property/name -> content
        for tag_attrs in meta_tags:
            # Extract content attribute
            content_m = re.search(r'content\s*=\s*["\']([^"\']*)["\']', tag_attrs, re.IGNORECASE)
            if not content_m:
                continue
            content = content_m.group(1)

            # Extract property or name attribute
            prop_m = re.search(r'(?:property|name)\s*=\s*["\']([^"\']*)["\']', tag_attrs, re.IGNORECASE)
            if not prop_m:
                continue
            prop = prop_m.group(1).lower()

            if prop not in meta_map:
                meta_map[prop] = content

        def _get(key: str) -> str:
            return meta_map.get(key, "")

        # Profile picture: og:image > twitter:image > twitter:image:src
        pic_url = _get("og:image") or _get("twitter:image") or _get("twitter:image:src")
        if pic_url and pic_url.startswith("http"):
            # Skip generic/default images
            skip_words = ["default", "logo", "favicon", "placeholder", "share", "open_graph"]
            is_generic = any(w in pic_url.lower() for w in skip_words)
            if not is_generic:
                data["profile_pic_url"] = pic_url
                data["profile_pic_data"] = _download_image(pic_url)

        # Bio: og:description > twitter:description > description
        bio = _get("og:description") or _get("twitter:description") or _get("description")
        if bio:
            data["bio"] = bio[:200]

        # Display name: og:title > twitter:title > <title> tag
        title = _get("og:title") or _get("twitter:title")
        if not title:
            m = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
            if m:
                title = m.group(1).strip()
        if title:
            data["display_name"] = title[:100]

    except Exception:
        pass
    return data


# ──────────────────────────────────────────────────────────────
#  Platform Enricher Registry
# ──────────────────────────────────────────────────────────────

PLATFORM_ENRICHERS = {
    "Instagram":    _enrich_instagram,
    "GitHub":       _enrich_github,
    "Reddit":       _enrich_reddit,
    "Gravatar":     _enrich_gravatar,
}

# Platforms where we can try OG-tag scraping as fallback
OG_ENRICHABLE = {
    "Medium", "Dev.to", "Hashnode", "Behance", "Dribbble",
    "500px", "DeviantArt", "ArtStation", "Kaggle", "HackerRank",
    "LeetCode", "ProductHunt", "Linktree", "About.me",
    "SoundCloud", "Bandcamp", "Letterboxd", "Goodreads",
    "Pinterest", "Twitch", "YouTube", "TikTok",
}


class ProfileEnricher:
    """Enriches found profiles with bio, followers, profile pictures."""

    def __init__(self, delay: float = 0.3):
        self.delay = delay
        self._stop = False

    def stop(self):
        self._stop = True

    def enrich(self, result: dict, callback=None) -> dict:
        """Enrich a single result with additional profile data."""
        if self._stop:
            return result

        platform = result.get("platform", "")
        username = result.get("username", "")

        if not username:
            url = result.get("url", "")
            parts = url.rstrip("/").split("/")
            username = parts[-1] if parts else ""
            username = username.lstrip("@")
            result["username"] = username

        # Try platform-specific enricher first
        enricher = PLATFORM_ENRICHERS.get(platform)
        if enricher and username:
            try:
                enriched = enricher(username)
                # Only update with non-empty values
                for k, v in enriched.items():
                    if v:
                        result[k] = v
                if callback:
                    has_data = bool(result.get("bio") or result.get("profile_pic_data"))
                    callback(
                        module="Enrichment",
                        message=f"Enriched {platform}: {username}" + (" [DATA FOUND]" if has_data else " [no data]"),
                        progress=0,
                        results=[],
                    )
            except Exception:
                pass
            time.sleep(self.delay)
            return result

        # For ALL other platforms: try OG-tag scraping from their URL
        url = result.get("url", "")
        if url and url.startswith("http"):
            try:
                og_data = _enrich_from_og_tags(url)
                for k, v in og_data.items():
                    if v:
                        result[k] = v
                if callback:
                    has_data = bool(result.get("bio") or result.get("profile_pic_data"))
                    callback(
                        module="Enrichment",
                        message=f"Scraped {platform}: {username}" + (" [DATA]" if has_data else " [no extra data]"),
                        progress=0,
                        results=[],
                    )
            except Exception:
                pass
            time.sleep(self.delay)

        return result

    def enrich_all(self, results: list[dict], callback=None) -> list[dict]:
        """Enrich all found profiles."""
        enrichable = [r for r in results if r.get("exists")]
        total = len(enrichable)

        for i, result in enumerate(enrichable):
            if self._stop:
                break
            self.enrich(result, callback)
            if callback:
                callback(
                    module="Enrichment",
                    message=f"[{i+1}/{total}] Enriching profiles...",
                    progress=int(((i + 1) / total) * 100) if total else 100,
                    results=[],
                )

        return results
