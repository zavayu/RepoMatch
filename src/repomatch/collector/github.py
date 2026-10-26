"""Serial GitHub requests with bounded retries and explicit rate-limit handling."""

from email.utils import parsedate_to_datetime
import json
import logging
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

LOG = logging.getLogger(__name__)
TRANSIENT_HTTP_STATUSES = {500, 502, 503, 504}


class GitHubError(RuntimeError):
    """A collection failure; status is None when no HTTP response was received."""

    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


class RateLimitError(GitHubError):
    """The run should pause until GitHub allows more requests."""


class NoRedirect(HTTPRedirectHandler):
    """Do not forward authenticated requests to API-provided redirect targets."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def retry_delay(headers, attempt, clock=time.time):
    """Prefer GitHub's wait instructions; otherwise use exponential backoff."""
    retry_after = headers.get("Retry-After")
    if retry_after:
        try:
            return max(0, float(retry_after)) + 1
        except ValueError:
            # Retry-After may be a date instead of a number of seconds.
            try:
                retry_at = parsedate_to_datetime(retry_after).timestamp()
                return max(0, retry_at - clock()) + 1
            except (ValueError, TypeError):
                pass

    if headers.get("X-RateLimit-Remaining") == "0":
        try:
            reset_at = float(headers["X-RateLimit-Reset"])
            return max(0, reset_at - clock()) + 1
        except (KeyError, ValueError):
            pass

    return min(2 ** attempt, 60)


def is_rate_limited(error, response_body: str) -> bool:
    """Distinguish rate-limited 403s from ordinary permission failures."""
    if error.code == 429:
        return True
    if error.code != 403:
        return False
    return (
        error.headers.get("X-RateLimit-Remaining") == "0"
        or error.headers.get("Retry-After") is not None
        or "rate limit" in response_body
    )


class GitHubClient:
    """Keep requests sequential and stop rather than wait indefinitely."""

    def __init__(
        self,
        token,
        config,
        *,
        opener=None,
        sleep=time.sleep,
        monotonic=time.monotonic,
    ):
        self.token = token
        self.config = config

        # Injected I/O and clocks let tests exercise retries without real waits.
        self.opener = opener or build_opener(NoRedirect())
        self.sleep = sleep
        self.monotonic = monotonic
        self.last_request = None

    def _pace_request(self):
        """Leave at least request_interval seconds between request starts."""
        if self.last_request is not None:
            elapsed = self.monotonic() - self.last_request
            remaining = max(0, self.config.request_interval - elapsed)
            self.sleep(remaining)
        self.last_request = self.monotonic()

    def get(self, path, params=None, *, allow_missing=False):
        """Return parsed JSON, or None for an explicitly allowed 404 response."""
        if not path.startswith("/") or "://" in path or "?" in path:
            raise ValueError("Expected a relative GitHub API path")

        url = "https://api.github.com" + path
        if params:
            url += "?" + urlencode(params)

        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "RepoMatch-collector",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = "Bearer " + self.token

        # retries counts additional attempts after the initial request.
        for attempt in range(self.config.retries + 1):
            self._pace_request()
            request = Request(url, headers=headers)

            try:
                with self.opener.open(
                    request, timeout=self.config.timeout
                ) as response:
                    return json.load(response)
            except HTTPError as error:
                if error.code == 404 and allow_missing:
                    error.close()
                    return None

                # Inspect only enough body text to identify secondary limits.
                # Do not log the response body or authentication headers.
                body = error.read(8192).decode("utf-8", errors="replace").lower()
                error.close()
                limited = is_rate_limited(error, body)
                transient = error.code in TRANSIENT_HTTP_STATUSES
                if not limited and not transient:
                    raise GitHubError(
                        f"GitHub returned HTTP {error.code} for {path}",
                        error.code,
                    ) from None

                wait = retry_delay(error.headers, attempt)
                no_attempts_left = attempt == self.config.retries
                wait_too_long = wait > self.config.max_wait
                if no_attempts_left or wait_too_long:
                    error_type = RateLimitError if limited else GitHubError
                    raise error_type(
                        f"GitHub HTTP {error.code}; retry later "
                        f"(wait {wait:.0f}s). Progress is saved.",
                        error.code,
                    ) from None

            except (URLError, TimeoutError, ConnectionError, OSError):
                wait = min(2 ** attempt, 60)
                if attempt == self.config.retries:
                    raise GitHubError(
                        f"Network request failed for {path}"
                    ) from None

            except (json.JSONDecodeError, UnicodeDecodeError):
                raise GitHubError(f"Invalid JSON response for {path}") from None

            LOG.warning("Retrying %s in %.0fs", path, wait)
            self.sleep(wait)

        raise AssertionError("unreachable")

