"""
╔══════════════════════════════════════════════════════════════╗
║  Email Lookup — Gravatar, LeakCheck, HIBP, 30+ Site Checks  ║
║  Checks which sites/services an email is linked to          ║
╚══════════════════════════════════════════════════════════════╝
"""

import hashlib
import os
import re
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional


class EmailLookup:
    """
    Performs email-based OSINT:
      1. Gravatar check (profile pic + bio)
      2. LeakCheck breach check (free public API)
      3. HaveIBeenPwned breach check (optional, paid)
      4. 30+ site registration checks
    """

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
    }
    TIMEOUT = 10

    # ──────────────────────────────────────────────────────────
    #  Sites to check — password reset / signup endpoints
    #  that reveal whether an email is registered
    # ──────────────────────────────────────────────────────────

    EMAIL_SITES = [
        # ── Social & Media ─────────────────────────────────────
        {"platform": "Spotify", "url": "https://spclient.wg.spotify.com/signup/public/v1/account?validate=1&email={email}",
         "check": "status_20"},
        {"platform": "Twitter / X", "url": "https://api.twitter.com/i/users/email_available.json?email={email}",
         "check": "not_valid"},
        {"platform": "Pinterest", "url": "https://www.pinterest.com/resource/EmailExistsResource/get/?source_url=/&data=%7B%22options%22%3A%7B%22email%22%3A%22{email}%22%7D%7D",
         "check": "resource_exists"},
        {"platform": "Imgur", "url": "https://imgur.com/signin/ajax_email_check?email={email}",
         "check": "taken"},
        {"platform": "WordPress", "url": "https://public-api.wordpress.com/rest/v1.1/users/suggest?q={email}",
         "check": "api_200"},
        {"platform": "Adobe", "url": "https://auth.services.adobe.com/signin/v2/users/accounts?email_id={email}",
         "check": "api_200"},
        {"platform": "Samsung", "url": "https://account.samsung.com/membership/api/v1/email/check?emailID={email}",
         "check": "api_200"},
        {"platform": "Firefox / Mozilla", "url": "https://api.accounts.firefox.com/v1/account/status",
         "check": "firefox", "method": "post"},
        {"platform": "Duolingo", "url": "https://www.duolingo.com/2017-06-30/users?email={email}",
         "check": "api_users"},
        {"platform": "Gravatar", "url": "https://en.gravatar.com/{hash}.json",
         "check": "api_200", "use_hash": True},

        # ── Developer & Tech ──────────────────────────────────
        {"platform": "GitHub", "url": "https://api.github.com/search/users?q={email}+in:email",
         "check": "github"},
        {"platform": "GitLab", "url": "https://gitlab.com/api/v4/users?search={email}",
         "check": "api_list"},
        {"platform": "npm", "url": "https://www.npmjs.com/signup/check-email?email={email}",
         "check": "taken"},
        {"platform": "Docker Hub", "url": "https://hub.docker.com/v2/users/?username={local}",
         "check": "api_200", "use_local": True},
        {"platform": "Replit", "url": "https://replit.com/data/user/exists/{local}",
         "check": "taken", "use_local": True},

        # ── Shopping & Services ────────────────────────────────
        {"platform": "eBay", "url": "https://signin.ebay.com/ws/eBayISAPI.dll?SignIn&email={email}",
         "check": "page_exists"},
        {"platform": "Etsy", "url": "https://www.etsy.com/api/v3/ajax/member/email-check?email={email}",
         "check": "taken"},
        {"platform": "Flipkart", "url": "https://www.flipkart.com/api/6/user/account-details?email={email}",
         "check": "api_200"},
        {"platform": "Booking.com", "url": "https://account.booking.com/api/identity/check?email={email}",
         "check": "api_200"},

        # ── Gaming ─────────────────────────────────────────────
        {"platform": "Steam", "url": "https://store.steampowered.com/join/ajaxverifyemail",
         "check": "steam", "method": "post"},
        {"platform": "Epic Games", "url": "https://www.epicgames.com/account/api/account/search?email={email}",
         "check": "api_200"},
        {"platform": "Xbox / Microsoft", "url": "https://login.live.com/GetCredentialType.srf",
         "check": "microsoft", "method": "post"},
        {"platform": "Chess.com", "url": "https://www.chess.com/callback/email/available?email={email}",
         "check": "not_available"},

        # ── Education ──────────────────────────────────────────
        {"platform": "Codecademy", "url": "https://www.codecademy.com/api/users?email={email}",
         "check": "api_list"},
        {"platform": "Coursera", "url": "https://api.coursera.org/api/accountExists.v1?email={email}",
         "check": "api_200"},

        # ── Other ──────────────────────────────────────────────
        {"platform": "Zoom", "url": "https://zoom.us/account/user/validate_email?email={email}",
         "check": "api_200"},
        {"platform": "Dropbox", "url": "https://www.dropbox.com/login/ajax_email_check?email={email}",
         "check": "taken"},
        {"platform": "Slack", "url": "https://slack.com/api/users.admin.checkEmail?email={email}",
         "check": "api_200"},
        {"platform": "Notion", "url": "https://www.notion.so/api/v3/getSpaces",
         "check": "api_200"},
        {"platform": "Canva", "url": "https://www.canva.com/_ajax/login/email_check?email={email}",
         "check": "api_200"},
        {"platform": "Discord", "url": "https://discord.com/api/v9/auth/register",
         "check": "discord", "method": "post"},
    ]

    def __init__(self, hibp_api_key: Optional[str] = None):
        if not hibp_api_key:
            try:
                from config import HIBP_API_KEY
                hibp_api_key = HIBP_API_KEY
            except ImportError:
                pass
        self.hibp_api_key = hibp_api_key or os.environ.get("HIBP_API_KEY", "")
        self.results: list[dict] = []
        self._stop_flag = False

    def stop(self):
        self._stop_flag = True

    # ──────────────────────────────────────────────────────────
    #  Gravatar Check (with profile pic download)
    # ──────────────────────────────────────────────────────────

    def check_gravatar(self, email: str) -> dict:
        """Check if the email has an associated Gravatar profile."""
        email_hash = hashlib.md5(email.strip().lower().encode()).hexdigest()
        profile_url = f"https://en.gravatar.com/{email_hash}.json"
        avatar_url = f"https://www.gravatar.com/avatar/{email_hash}?d=404&s=400"

        result = {
            "platform": "Gravatar",
            "url": profile_url,
            "exists": False,
            "display_name": "",
            "bio": "",
            "username": email.split("@")[0],
            "source": "email_lookup",
            "category": "profile",
        }

        try:
            resp = requests.get(profile_url, headers=self.HEADERS, timeout=self.TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                entry = data.get("entry", [{}])[0]
                result["exists"] = True
                result["display_name"] = entry.get("displayName", "")
                result["bio"] = entry.get("aboutMe", "") or ""
                result["url"] = entry.get("profileUrl", profile_url)
                result["profile_pic_url"] = entry.get("thumbnailUrl", avatar_url)
                if result["profile_pic_url"]:
                    result["profile_pic_url"] = result["profile_pic_url"].split("?")[0] + "?s=400"
                try:
                    pic = requests.get(result.get("profile_pic_url", avatar_url),
                                       headers=self.HEADERS, timeout=6)
                    if pic.status_code == 200:
                        result["profile_pic_data"] = pic.content
                except Exception:
                    pass
            else:
                try:
                    avatar_resp = requests.get(avatar_url, headers=self.HEADERS, timeout=6)
                    if avatar_resp.status_code == 200:
                        result["exists"] = True
                        result["profile_pic_url"] = avatar_url
                        result["profile_pic_data"] = avatar_resp.content
                except Exception:
                    pass
        except Exception:
            pass

        return result

    # ──────────────────────────────────────────────────────────
    #  HaveIBeenPwned Check
    # ──────────────────────────────────────────────────────────

    def check_hibp(self, email: str) -> dict:
        result = {
            "platform": "HaveIBeenPwned",
            "url": f"https://haveibeenpwned.com/account/{email}",
            "exists": False,
            "bio": "",
            "username": email,
            "source": "email_lookup",
            "category": "mention",
        }

        if not self.hibp_api_key:
            result["bio"] = "HIBP API key not configured - skipped"
            return result

        try:
            url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
            headers = {**self.HEADERS, "hibp-api-key": self.hibp_api_key}
            resp = requests.get(url, headers=headers, timeout=self.TIMEOUT,
                                params={"truncateResponse": "false"})
            if resp.status_code == 200:
                breaches = resp.json()
                result["exists"] = True
                names = [b.get("Name", "") for b in breaches[:8]]
                result["bio"] = f"BREACHED in {len(breaches)} sites: {', '.join(names)}"
            elif resp.status_code == 404:
                result["bio"] = "No breaches found - email is clean"
        except Exception as e:
            result["bio"] = f"HIBP error: {e}"

        return result

    # ──────────────────────────────────────────────────────────
    #  LeakCheck Public API (FREE)
    # ──────────────────────────────────────────────────────────

    def check_leakcheck(self, email: str) -> dict:
        """Check email against LeakCheck free public API for breach data."""
        result = {
            "platform": "LeakCheck",
            "url": f"https://leakcheck.io/",
            "exists": False,
            "bio": "",
            "username": email,
            "source": "email_lookup",
            "category": "mention",
            "breach_data": None,
        }

        try:
            api_url = f"https://leakcheck.io/api/public?check={email}"
            resp = requests.get(api_url, headers=self.HEADERS, timeout=self.TIMEOUT)

            if resp.status_code == 200:
                data = resp.json()
                if data.get("success") and data.get("found", 0) > 0:
                    found_count = data["found"]
                    sources = data.get("sources", [])
                    fields = data.get("fields", [])

                    result["exists"] = True
                    result["category"] = "mention"

                    # Build source summary (top 10 for bio)
                    source_names = []
                    for s in sources[:10]:
                        name = s.get("name", "Unknown")
                        date = s.get("date", "")
                        if date:
                            source_names.append(f"{name} ({date})")
                        else:
                            source_names.append(name)

                    result["bio"] = (
                        f"⚠ BREACHED in {found_count} databases! "
                        f"Top sources: {', '.join(source_names)}"
                    )
                    if len(sources) > 10:
                        result["bio"] += f" ... and {len(sources) - 10} more"

                    # Store full breach data for the GUI card
                    result["breach_data"] = {
                        "email": email,
                        "total_breaches": found_count,
                        "total_sources": len(sources),
                        "fields_exposed": fields,
                        "sources": sources,
                    }
                else:
                    result["bio"] = "No breaches found — email is clean ✓"
            elif resp.status_code == 429:
                result["bio"] = "LeakCheck rate limited — try again later"
            else:
                result["bio"] = f"LeakCheck returned status {resp.status_code}"

        except requests.exceptions.Timeout:
            result["bio"] = "LeakCheck request timed out"
        except requests.exceptions.ConnectionError:
            result["bio"] = "LeakCheck connection error — check network"
        except Exception as e:
            result["bio"] = f"LeakCheck error: {e}"

        return result

    # ──────────────────────────────────────────────────────────
    #  Single Site Check
    # ──────────────────────────────────────────────────────────

    def _check_single_site(self, site: dict, email: str) -> dict:
        """Check if email is registered on a single site."""
        platform = site["platform"]
        email_hash = hashlib.md5(email.strip().lower().encode()).hexdigest()
        local_part = email.split("@")[0]

        url = site["url"].replace("{email}", email)
        if site.get("use_hash"):
            url = url.replace("{hash}", email_hash)
        if site.get("use_local"):
            url = url.replace("{local}", local_part)

        result = {
            "platform": platform,
            "url": "",
            "exists": False,
            "username": email,
            "bio": "",
            "source": "email_lookup",
            "category": "profile",
        }

        try:
            method = site.get("method", "get")
            check = site["check"]

            if method == "post":
                # POST-based checks
                if platform == "Firefox / Mozilla":
                    resp = requests.post(url,
                        json={"email": email},
                        headers={**self.HEADERS, "Content-Type": "application/json"},
                        timeout=self.TIMEOUT)
                    if resp.status_code == 200:
                        j = resp.json()
                        if j.get("exists"):
                            result["exists"] = True
                            result["bio"] = "Email registered with Firefox/Mozilla account"
                            result["url"] = "https://accounts.firefox.com"

                elif platform == "Steam":
                    resp = requests.post(url,
                        data={"email": email},
                        headers=self.HEADERS, timeout=self.TIMEOUT)
                    if resp.status_code == 200:
                        body = resp.text.lower()
                        if "in use" in body or "already" in body:
                            result["exists"] = True
                            result["bio"] = "Email registered on Steam"
                            result["url"] = "https://store.steampowered.com"

                elif platform == "Xbox / Microsoft":
                    resp = requests.post(url,
                        json={"username": email, "uaid": "", "isOtherIdpSupported": True},
                        headers={**self.HEADERS, "Content-Type": "application/json"},
                        timeout=self.TIMEOUT)
                    if resp.status_code == 200:
                        j = resp.json()
                        if j.get("IfExistsResult") == 0:  # 0 = exists
                            result["exists"] = True
                            result["bio"] = "Email registered with Microsoft account"
                            result["url"] = "https://account.microsoft.com"

                elif platform == "Discord":
                    resp = requests.post(url,
                        json={"email": email, "username": "test123456789", "password": "Test@12345678", "date_of_birth": "1990-01-01"},
                        headers={**self.HEADERS, "Content-Type": "application/json"},
                        timeout=self.TIMEOUT)
                    if resp.status_code == 400:
                        j = resp.json()
                        errors = j.get("errors", {})
                        if "email" in errors:
                            msgs = str(errors["email"]).lower()
                            if "already" in msgs or "registered" in msgs or "taken" in msgs:
                                result["exists"] = True
                                result["bio"] = "Email registered on Discord"
                                result["url"] = "https://discord.com"
                else:
                    resp = requests.post(url, json={"email": email},
                        headers={**self.HEADERS, "Content-Type": "application/json"},
                        timeout=self.TIMEOUT)

            else:
                # GET-based checks
                resp = requests.get(url, headers=self.HEADERS, timeout=self.TIMEOUT)

                if check == "github":
                    if resp.status_code == 200:
                        items = resp.json().get("items", [])
                        if items:
                            result["exists"] = True
                            user = items[0]
                            result["url"] = user.get("html_url", "")
                            result["username"] = user.get("login", email)
                            result["display_name"] = user.get("login", "")
                            result["profile_pic_url"] = user.get("avatar_url", "")
                            result["bio"] = f"GitHub: {result['username']}"
                            if result["profile_pic_url"]:
                                try:
                                    pic = requests.get(result["profile_pic_url"],
                                                       headers=self.HEADERS, timeout=6)
                                    if pic.status_code == 200:
                                        result["profile_pic_data"] = pic.content
                                except Exception:
                                    pass

                elif check == "status_20":
                    if resp.status_code == 200:
                        j = resp.json()
                        if j.get("status") == 20:
                            result["exists"] = True
                            result["bio"] = f"Email registered on {platform}"
                            result["url"] = f"https://open.spotify.com"

                elif check == "not_valid":
                    if resp.status_code == 200:
                        j = resp.json()
                        if not j.get("valid", True):
                            result["exists"] = True
                            result["bio"] = f"Email registered on {platform}"
                            result["url"] = "https://x.com"

                elif check == "not_available":
                    if resp.status_code == 200:
                        body = resp.text.lower()
                        if "false" in body or "not available" in body or "taken" in body:
                            result["exists"] = True
                            result["bio"] = f"Email registered on {platform}"

                elif check == "taken":
                    if resp.status_code == 200:
                        body = resp.text.lower()
                        if "true" in body or "taken" in body or "exists" in body or "unavailable" in body:
                            result["exists"] = True
                            result["bio"] = f"Email registered on {platform}"

                elif check == "api_list":
                    if resp.status_code == 200:
                        j = resp.json()
                        if isinstance(j, list) and len(j) > 0:
                            result["exists"] = True
                            if j[0].get("username"):
                                result["username"] = j[0]["username"]
                                result["bio"] = f"{platform}: {result['username']}"
                            if j[0].get("avatar_url"):
                                result["profile_pic_url"] = j[0]["avatar_url"]
                            result["url"] = j[0].get("web_url", "")

                elif check == "api_users":
                    if resp.status_code == 200:
                        j = resp.json()
                        users = j.get("users", [])
                        if users:
                            result["exists"] = True
                            u = users[0]
                            result["username"] = u.get("username", email)
                            result["bio"] = f"{platform}: {result['username']}"
                            result["url"] = f"https://www.duolingo.com/profile/{result['username']}"

                elif check == "resource_exists":
                    if resp.status_code == 200:
                        body = resp.text
                        if '"account_type"' in body or '"email_exists":true' in body.lower() or '"resource_data_cache"' in body:
                            result["exists"] = True
                            result["bio"] = f"Email registered on {platform}"
                            result["url"] = "https://pinterest.com"

                elif check == "api_200":
                    if resp.status_code == 200:
                        body = resp.text.lower()
                        neg = ["not found", "not exist", "no user", "error", "invalid"]
                        if not any(n in body for n in neg):
                            result["exists"] = True
                            result["bio"] = f"Email linked to {platform}"

                elif check == "page_exists":
                    if resp.status_code == 200:
                        result["exists"] = True
                        result["bio"] = f"Email linked to {platform}"

            # Set default URL if found but no URL set
            if result["exists"] and not result["url"]:
                result["url"] = url.split("?")[0]

        except Exception:
            pass

        return result

    def check_email_sites(self, email: str, callback=None) -> list[dict]:
        """Check multiple sites for email registration using threading."""
        results = []
        total = len(self.EMAIL_SITES)
        completed = 0

        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {}
            for site in self.EMAIL_SITES:
                if self._stop_flag:
                    break
                future = executor.submit(self._check_single_site, site, email)
                futures[future] = site["platform"]

            for future in as_completed(futures):
                if self._stop_flag:
                    break
                result = future.result()
                results.append(result)
                completed += 1

                if callback:
                    status = "LINKED" if result["exists"] else "not found"
                    callback(
                        module="Email Lookup",
                        message=f"[{completed}/{total}] {result['platform']} - {status}",
                        progress=int((completed / total) * 100),
                        results=[result] if result["exists"] else [],
                    )
                time.sleep(0.1)

        return results

    # ──────────────────────────────────────────────────────────
    #  Full Email Scan
    # ──────────────────────────────────────────────────────────

    def scan(self, email: str, callback=None) -> list[dict]:
        """Run the full email investigation pipeline."""
        self._stop_flag = False
        all_results = []

        # Step 1: Gravatar
        if not self._stop_flag:
            if callback:
                callback(module="Email Lookup", message="[1/4] Checking Gravatar...",
                         progress=5, results=[])
            grav = self.check_gravatar(email)
            all_results.append(grav)
            if callback:
                found = [grav] if grav["exists"] else []
                callback(module="Email Lookup",
                         message=f"[1/4] Gravatar — {'FOUND!' if grav['exists'] else 'not found'}",
                         progress=15, results=found)

        # Step 2: LeakCheck (FREE breach API)
        if not self._stop_flag:
            if callback:
                callback(module="Email Lookup", message="[2/4] Checking LeakCheck breaches...",
                         progress=20, results=[])
            leak = self.check_leakcheck(email)
            all_results.append(leak)
            if callback:
                if leak["exists"]:
                    bd = leak.get("breach_data", {})
                    total = bd.get("total_breaches", 0) if bd else 0
                    callback(module="Email Lookup",
                             message=f"[2/4] LeakCheck — ⚠ BREACHED in {total} databases!",
                             progress=30, results=[leak])
                else:
                    callback(module="Email Lookup",
                             message=f"[2/4] LeakCheck — {leak['bio']}",
                             progress=30, results=[])

        # Step 3: HIBP (paid API, optional)
        if not self._stop_flag:
            if callback:
                callback(module="Email Lookup", message="[3/4] Checking HaveIBeenPwned...",
                         progress=35, results=[])
            hibp = self.check_hibp(email)
            all_results.append(hibp)
            if callback and hibp["exists"]:
                callback(module="Email Lookup",
                         message=f"[3/4] HIBP — BREACHED!",
                         progress=40, results=[hibp])

        # Step 4: Site registration checks (30+ sites)
        if not self._stop_flag:
            if callback:
                callback(module="Email Lookup",
                         message=f"[4/4] Checking {len(self.EMAIL_SITES)} sites for registration...",
                         progress=45, results=[])
            site_results = self.check_email_sites(email, callback)
            all_results.extend(site_results)

            # Summary
            linked = [r for r in site_results if r["exists"]]
            if callback:
                if linked:
                    names = ", ".join(r["platform"] for r in linked)
                    callback(module="Email Lookup",
                             message=f"Email linked to {len(linked)} sites: {names}",
                             progress=100, results=[])
                else:
                    callback(module="Email Lookup",
                             message="No site registrations detected",
                             progress=100, results=[])

        self.results = all_results
        return all_results
