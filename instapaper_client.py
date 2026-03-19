import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import requests
from requests_oauthlib import OAuth1


API_BASE = "https://www.instapaper.com/api/1"


class InstapaperError(Exception):
    pass


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise InstapaperError(f"Missing required environment variable: {name}")
    return value


def _parse_qline(line: str) -> Dict[str, str]:
    parts = line.strip().split("&")
    result: Dict[str, str] = {}
    for pair in parts:
        if "=" in pair:
            k, v = pair.split("=", 1)
            result[k] = requests.utils.unquote(v)
    return result


@dataclass
class InstapaperCredentials:
    oauth_token: str
    oauth_token_secret: str


class InstapaperClient:
    def __init__(self, consumer_key: str, consumer_secret: str):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

    @classmethod
    def from_env(cls) -> "InstapaperClient":
        key = _require_env("INSTAPAPER_CONSUMER_KEY")
        secret = _require_env("INSTAPAPER_CONSUMER_SECRET")
        return cls(key, secret)

    def _oauth(self, token: str | None = None, token_secret: str | None = None) -> OAuth1:
        return OAuth1(
            self.consumer_key,
            client_secret=self.consumer_secret,
            resource_owner_key=token,
            resource_owner_secret=token_secret,
            signature_method="HMAC-SHA1",
        )

    def get_access_token(self, username: str, password: str) -> InstapaperCredentials:
        url = f"{API_BASE}/oauth/access_token"
        data = {
            "x_auth_mode": "client_auth",
            "x_auth_username": username,
            "x_auth_password": password,
        }
        resp = requests.post(url, data=data, auth=self._oauth())
        if resp.status_code != 200:
            raise InstapaperError("Instapaper login failed.")
        parsed = _parse_qline(resp.text)
        token = parsed.get("oauth_token")
        secret = parsed.get("oauth_token_secret")
        if not token or not secret:
            raise InstapaperError("Invalid response from Instapaper when obtaining token.")
        return InstapaperCredentials(oauth_token=token, oauth_token_secret=secret)

    def list_bookmarks(
        self,
        creds: InstapaperCredentials,
        folder_id: str = "unread",
        limit: int = 25,
    ) -> Dict[str, Any]:
        url = f"{API_BASE}/bookmarks/list"
        data = {"folder_id": folder_id, "limit": limit}
        resp = requests.post(url, data=data, auth=self._oauth(creds.oauth_token, creds.oauth_token_secret))
        if resp.status_code != 200:
            raise InstapaperError("Failed to fetch bookmarks from Instapaper.")
        raw = resp.json()

        # The API may return either a JSON object with {user, bookmarks, ...}
        # or the older array-of-objects format. Normalize to a dict.
        if isinstance(raw, list):
            user = None
            bookmarks: list[Dict[str, Any]] = []
            for item in raw:
                if not isinstance(item, dict):
                    continue
                t = item.get("type")
                if t == "user" and user is None:
                    user = item
                elif t == "bookmark":
                    bookmarks.append(item)
            return {"user": user, "bookmarks": bookmarks}

        return raw

    def get_text(self, creds: InstapaperCredentials, bookmark_id: int) -> str:
        url = f"{API_BASE}/bookmarks/get_text"
        data = {"bookmark_id": bookmark_id}
        resp = requests.post(url, data=data, auth=self._oauth(creds.oauth_token, creds.oauth_token_secret))
        if resp.status_code != 200:
            raise InstapaperError("Failed to fetch article text from Instapaper.")
        return resp.text

    def archive(self, creds: InstapaperCredentials, bookmark_id: int) -> Dict[str, Any]:
        url = f"{API_BASE}/bookmarks/archive"
        data = {"bookmark_id": bookmark_id}
        resp = requests.post(url, data=data, auth=self._oauth(creds.oauth_token, creds.oauth_token_secret))
        if resp.status_code != 200:
            raise InstapaperError("Failed to archive bookmark.")
        return resp.json()

    def update_read_progress(
        self,
        creds: InstapaperCredentials,
        bookmark_id: int,
        progress: float,
    ) -> Dict[str, Any]:
        url = f"{API_BASE}/bookmarks/update_read_progress"
        data = {
            "bookmark_id": bookmark_id,
            "progress": progress,
            "progress_timestamp": int(time.time()),
        }
        resp = requests.post(url, data=data, auth=self._oauth(creds.oauth_token, creds.oauth_token_secret))
        if resp.status_code != 200:
            raise InstapaperError("Failed to update read progress.")
        return resp.json()

