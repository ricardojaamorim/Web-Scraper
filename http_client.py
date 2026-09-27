import time
import urllib.robotparser
from urllib.parse import urljoin

import requests

from config import MIN_DELAY_SECONDS


class RobotsChecker:
    """Wraps urllib.robotparser so every fetch is checked against robots.txt."""

    def __init__(self, base_url: str, user_agent: str):
        self.user_agent = user_agent
        self.parser = urllib.robotparser.RobotFileParser()
        self.parser.set_url(urljoin(base_url, "/robots.txt"))
        self.parser.read()
        # crawl_delay() returns None if the site doesn't specify one
        self.crawl_delay = self.parser.crawl_delay(user_agent) or MIN_DELAY_SECONDS

    def can_fetch(self, url: str) -> bool:
        return self.parser.can_fetch(self.user_agent, url)


class RateLimitedSession:
    """A requests.Session that enforces a minimum delay between calls."""

    def __init__(self, user_agent: str, delay: float):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self.delay = delay
        self._last_request_time = 0.0

    def get(self, url: str, **kwargs) -> requests.Response | None:
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        try:
            response = self.session.get(url, timeout=15, **kwargs)
            self._last_request_time = time.monotonic()
            response.raise_for_status()
            # Pingo Doce's pages are UTF-8, but don't always declare it clearly
            # in headers
            response.encoding = "utf-8"
            return response
        except requests.RequestException as e:
            print(f"  [error] fetching {url}: {e}")
            return None
