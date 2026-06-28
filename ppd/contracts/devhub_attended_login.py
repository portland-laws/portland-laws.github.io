"""Attended DevHub login contract for PP&D automation boundaries.

This module describes what automation may observe around Portland DevHub login.
It deliberately does not store browser state, credentials, MFA material, cookies,
tokens, traces, or raw authenticated crawl output.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


class DevHubLoginState(str, Enum):
    """Observable login states that do not require credential capture."""

    MANUAL_SIGN_IN_REQUIRED = "manual_sign_in_required"
    AUTHENTICATED = "authenticated"
    SAVE_RESUME_READY = "save_resume_ready"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class RedactedRouteSnapshot:
    """A route-only observation safe to commit or compare in tests."""

    method: str
    url: str
    status_code: int | None = None
    state: DevHubLoginState = DevHubLoginState.MANUAL_SIGN_IN_REQUIRED


@dataclass(frozen=True)
class AttendedDevHubLoginContract:
    """Policy for attended PortlandOregon.gov DevHub login handoff."""

    allowed_hosts: Sequence[str] = (
        "www.portlandoregon.gov",
        "aca.portlandoregon.gov",
        "devhub.portlandoregon.gov",
    )
    authenticated_markers: Sequence[str] = (
        "sign out",
        "log out",
        "logout",
        "my account",
        "dashboard",
        "permit applications",
    )
    manual_login_markers: Sequence[str] = (
        "sign in",
        "log in",
        "login",
        "password",
        "username",
    )
    blocked_markers: Sequence[str] = (
        "captcha",
        "multi-factor",
        "multifactor",
        "verification code",
        "one-time code",
        "payment",
        "certify",
        "submit application",
        "upload document",
    )
    sensitive_query_keys: Sequence[str] = (
        "access_token",
        "auth",
        "code",
        "cookie",
        "id_token",
        "key",
        "password",
        "refresh_token",
        "secret",
        "session",
        "state",
        "ticket",
        "token",
    )

    def state_from_observation(
        self,
        url: str,
        html_text: str = "",
        status_code: int | None = None,
    ) -> DevHubLoginState:
        """Classify a page observation without collecting credentials."""

        parsed = urlsplit(url)
        if parsed.hostname not in self.allowed_hosts:
            return DevHubLoginState.BLOCKED
        if status_code in {401, 403}:
            return DevHubLoginState.MANUAL_SIGN_IN_REQUIRED

        text = html_text.casefold()
        if any(marker in text for marker in self.blocked_markers):
            return DevHubLoginState.BLOCKED
        if any(marker in text for marker in self.authenticated_markers):
            if "save" in text and "resume" in text:
                return DevHubLoginState.SAVE_RESUME_READY
            return DevHubLoginState.AUTHENTICATED
        if any(marker in text for marker in self.manual_login_markers):
            return DevHubLoginState.MANUAL_SIGN_IN_REQUIRED
        return DevHubLoginState.MANUAL_SIGN_IN_REQUIRED

    def redacted_route_snapshot(
        self,
        url: str,
        method: str = "GET",
        html_text: str = "",
        status_code: int | None = None,
    ) -> RedactedRouteSnapshot:
        """Return a query-redacted route snapshot for deterministic fixtures."""

        return RedactedRouteSnapshot(
            method=method.upper(),
            url=self._redact_url(url),
            status_code=status_code,
            state=self.state_from_observation(url, html_text, status_code),
        )

    def assert_safe_metadata(self, metadata: Mapping[str, object]) -> None:
        """Reject metadata that looks like credential or browser-state capture."""

        unsafe_fragments = (
            "access_token",
            "auth_state",
            "browser_state",
            "cookie",
            "credential",
            "id_token",
            "mfa",
            "password",
            "refresh_token",
            "session_file",
            "storage_state",
            "token",
        )
        for key in metadata:
            normalized = key.casefold().replace("-", "_")
            if any(fragment in normalized for fragment in unsafe_fragments):
                raise ValueError(f"unsafe DevHub login metadata field: {key}")

    def can_save_resume(self, state: DevHubLoginState) -> bool:
        """Only explicit authenticated save/resume pages cross this boundary."""

        return state is DevHubLoginState.SAVE_RESUME_READY

    def _redact_url(self, url: str) -> str:
        parsed = urlsplit(url)
        if parsed.hostname not in self.allowed_hosts:
            return "blocked://external-route"

        query_pairs = []
        for key, value in parse_qsl(parsed.query, keep_blank_values=True):
            if self._is_sensitive_query_key(key):
                query_pairs.append((key, "REDACTED"))
            elif value:
                query_pairs.append((key, "VALUE"))
            else:
                query_pairs.append((key, ""))

        return urlunsplit(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                urlencode(query_pairs),
                "",
            )
        )

    def _is_sensitive_query_key(self, key: str) -> bool:
        normalized = key.casefold()
        return any(fragment in normalized for fragment in self.sensitive_query_keys)
