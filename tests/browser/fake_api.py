"""A stand-in for the server's API, used by the browser tests.

The real files in web/ are served to a real (headless) Chromium from a tiny
local web server. The FastAPI app is not started: every request the page makes
to /query, /reset, /sectors and /documents is answered by the FakeApi below, so
the tests need no API key, no Qdrant and no models, and each one runs in about
a second. Any other request is aborted, so a test can never reach the internet.

The page loads `marked` from a CDN. The same library is served from
tests/browser/vendor instead (see its version in the file header), so a test
result never depends on what the CDN is serving that day.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from playwright.sync_api import Page, Route

MARKED_JS = Path(__file__).parent / "vendor/marked.umd.js"

SECTORS = {
    "class_1": "Class 1 – Deposit taking",
    "class_4": "Class 4 – Corporate services",
    "class_5": "Class 5 – Trust services",
    "estate_agent": "Estate agent",
}

DOCUMENTS = [
    {"name": "Proceeds of Crime Act 2008", "hierarchy": "Primary legislation"},
    {"name": "The AML/CFT Code 2019", "hierarchy": "Secondary legislation"},
    {"name": "Business Risk Assessment guidance", "hierarchy": "Guidance"},
]


def sse(*events: tuple[str, Any]) -> str:
    """Build a /query reply body: an event name and a json (or plain text) payload each."""
    body = ""
    for name, payload in events:
        data = payload if isinstance(payload, str) else json.dumps(payload)
        body += f"event: {name}\ndata: {data}\n\n"
    return body


def citation(**overrides: Any) -> dict[str, Any]:
    cited = {
        "document": "The AML/CFT Code 2019",
        "headers": ["PART 4 - CUSTOMER DUE DILIGENCE", "Enhanced measures"],
        "url": "https://www.iomfsa.im/code.pdf",
        "relevance": "Sets out when enhanced due diligence applies.",
    }
    cited.update(overrides)
    return cited


def answer_event(
    answer: str = "Enhanced due diligence applies to **higher risk** customers.",
    citations: list[dict[str, Any]] | None = None,
) -> tuple[str, Any]:
    return ("answer", {"answer": answer, "citations": citations or [citation()]})


@dataclass
class FakeApi:
    """What the page's requests are answered with, and what it asked."""

    page: Page
    site_url: str
    sectors: dict[str, str] | None = field(default_factory=lambda: dict(SECTORS))
    documents: list[dict[str, str]] | None = field(
        default_factory=lambda: list(DOCUMENTS)
    )
    query_status: int = 200
    query_body: str = ""
    queries: list[dict[str, Any]] = field(default_factory=list)
    resets: list[dict[str, Any]] = field(default_factory=list)
    # with hold set, a /query request waits (the page shows its "working" state)
    # until release() is called
    hold: bool = False
    held: Route | None = None

    def reply_with(self, *events: tuple[str, Any], status: int = 200) -> None:
        self.query_body = sse(*events)
        self.query_status = status

    def release(self) -> None:
        route, self.held = self.held, None
        assert route is not None, "no /query request is being held"
        self.fulfill_query(route)

    def open(self) -> None:
        self.page.goto(self.site_url)
        # the welcome screen is drawn once the sector list and document list have loaded
        self.page.locator("#welcome").wait_for()

    def ask(self, question: str) -> None:
        self.page.locator("#prompt-input").fill(question)
        self.page.locator("#prompt-form button[type=submit]").click()

    def handle(self, route: Route) -> None:
        request = route.request
        url = urlsplit(request.url)
        host = urlsplit(self.site_url).netloc
        if url.netloc == host:
            self.handle_local(route, url.path)
        elif url.netloc == "cdn.jsdelivr.net" and "marked" in url.path:
            route.fulfill(
                body=MARKED_JS.read_text(encoding="utf-8"),
                content_type="application/javascript",
            )
        else:
            route.abort()

    def handle_local(self, route: Route, path: str) -> None:
        request = route.request
        if path == "/sectors":
            self.fulfill_json(route, self.sectors)
        elif path == "/documents":
            self.fulfill_json(route, self.documents)
        elif path == "/reset":
            self.resets.append(request.post_data_json)
            self.fulfill_json(route, {"status": "ok"})
        elif path == "/query":
            self.queries.append(request.post_data_json)
            if self.hold:
                self.held = route
            else:
                self.fulfill_query(route)
        else:
            route.continue_()

    def fulfill_query(self, route: Route) -> None:
        route.fulfill(
            status=self.query_status,
            body=self.query_body,
            content_type="text/event-stream",
        )

    @staticmethod
    def fulfill_json(route: Route, payload: Any) -> None:
        if payload is None:
            route.fulfill(status=500, body="down")
        else:
            route.fulfill(status=200, json=payload)
