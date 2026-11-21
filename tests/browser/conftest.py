"""Fixtures for the browser tests: the real web/ files served to a real
(headless) Chromium from a tiny local web server, with the server's API
replaced by tests/browser/fake_api.py. Nothing here reaches the internet."""

import functools
import http.server
import threading
from collections.abc import Iterator
from typing import Any

import pytest
from playwright.sync_api import BrowserContext, Page

from config import PROJECT_ROOT
from tests.browser.fake_api import FakeApi

WEB_DIR = PROJECT_ROOT / "web"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        pass


@pytest.fixture(scope="session")
def site_url() -> Iterator[str]:
    handler = functools.partial(QuietHandler, directory=str(WEB_DIR))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()


@pytest.fixture
def api(page: Page, context: BrowserContext, site_url: str) -> FakeApi:
    fake = FakeApi(page=page, site_url=site_url)
    context.route("**/*", fake.handle)
    return fake
