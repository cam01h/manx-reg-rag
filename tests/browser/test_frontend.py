"""The web/ front end, driven in a real browser against canned server replies.

Run with `uv run pytest -m browser` (needs `uv run playwright install chromium`
once). See conftest.py for how the server is faked. The tests find things by
`data-testid` or by the element ids in web/index.html, not by styling classes,
so a restyle does not break them.
"""

import re

import pytest
from playwright.sync_api import Page, expect

from tests.browser.fake_api import FakeApi, answer_event, citation

pytestmark = pytest.mark.browser

BASIC_PROGRESS = [
    ("search", {"term": "enhanced due diligence"}),
    (
        "read",
        {
            "document": "The AML/CFT Code 2019",
            "headers": "PART 4 - CUSTOMER DUE DILIGENCE, Enhanced measures",
        },
    ),
]


def tick(page: Page, *labels: str) -> None:
    if not page.locator("#sector-picker").evaluate("el => el.open"):
        page.locator("#sector-summary").click()
    for label in labels:
        page.get_by_label(label).check()


# ---- start-up --------------------------------------------------------------


def test_welcome_lists_documents_and_sectors_from_the_server(page: Page, api: FakeApi):
    api.open()
    expect(page.locator(".welcome-docs-count")).to_have_text("3 documents")
    expect(page.locator("#sector-options input[type=checkbox]")).to_have_count(4)
    expect(page.locator("#sector-summary")).to_have_text("Sectors: all")


def test_a_failed_sector_list_still_lets_questions_through(page: Page, api: FakeApi):
    api.sectors = None
    api.reply_with(answer_event())
    api.open()
    expect(page.locator("#sector-options")).to_contain_text(
        "Couldn't load the sector list"
    )
    api.ask("What is CDD?")
    expect(page.get_by_test_id("assistant-turn")).to_be_visible()
    assert api.queries[0]["sectors"] == []


def test_a_failed_document_list_just_leaves_it_out(page: Page, api: FakeApi):
    api.documents = None
    api.open()
    expect(page.locator(".welcome-docs")).to_have_count(0)
    expect(page.locator("#welcome")).to_be_visible()


# ---- asking a question -----------------------------------------------------


def test_answer_streams_in_with_progress_markdown_and_citations(
    page: Page, api: FakeApi
):
    api.reply_with(*BASIC_PROGRESS, answer_event())
    api.open()
    api.ask("When is enhanced due diligence needed?")

    expect(page.get_by_test_id("user-turn")).to_have_text(
        "When is enhanced due diligence needed?"
    )
    # markdown becomes markup
    expect(page.get_by_test_id("assistant-turn").locator("strong")).to_have_text(
        "higher risk"
    )
    expect(page.get_by_test_id("progress").locator(".progress-label")).to_have_text(
        "Query complete · 1 search, 1 section read"
    )
    expect(page.get_by_test_id("citation")).to_have_count(1)
    # the welcome screen goes away once a question is sent, and the box empties
    expect(page.locator("#welcome")).to_have_count(0)
    expect(page.locator("#prompt-input")).to_have_value("")


def test_while_a_query_runs_the_question_shows_and_a_second_send_is_ignored(
    page: Page, api: FakeApi
):
    api.reply_with(answer_event())
    api.hold = True
    api.open()
    api.ask("Is <b>this</b> text?")

    question = page.get_by_test_id("user-turn")
    expect(question).to_have_text("Is <b>this</b> text?")
    expect(question.locator("b")).to_have_count(0)
    expect(page.get_by_test_id("progress").locator(".progress-label")).to_have_text(
        "Searching the legislation…"
    )
    expect(page.locator("#prompt-form button[type=submit]")).to_be_disabled()
    expect(page.locator("#reset-button")).to_be_disabled()

    # Enter in the box must not start a second run of the agent
    page.locator("#prompt-input").fill("Again")
    page.locator("#prompt-input").press("Enter")
    page.wait_for_timeout(200)
    assert len(api.queries) == 1

    api.release()
    expect(page.get_by_test_id("assistant-turn")).to_be_visible()
    expect(page.locator("#prompt-form button[type=submit]")).to_be_enabled()
    assert len(api.queries) == 1


def test_request_carries_the_prompt_session_and_ticked_sectors(
    page: Page, api: FakeApi
):
    api.reply_with(answer_event())
    api.open()
    tick(page, "Class 4 – Corporate services", "Class 5 – Trust services")
    expect(page.locator("#sector-summary")).to_have_text("Sectors: 2 selected")
    api.ask("What is a PEP?")
    expect(page.get_by_test_id("assistant-turn")).to_be_visible()

    body = api.queries[0]
    assert body["prompt"] == "What is a PEP?"
    assert sorted(body["sectors"]) == ["class_4", "class_5"]
    assert body["session_id"] == page.evaluate("localStorage.getItem('session_id')")


def test_no_ticked_sectors_sends_an_empty_list(page: Page, api: FakeApi):
    api.reply_with(answer_event())
    api.open()
    api.ask("What is a PEP?")
    expect(page.get_by_test_id("assistant-turn")).to_be_visible()
    assert api.queries[0]["sectors"] == []


def test_ticked_sectors_are_remembered_after_a_reload(page: Page, api: FakeApi):
    api.open()
    tick(page, "Estate agent")
    page.reload()
    page.locator("#welcome").wait_for()
    expect(page.locator("#sector-summary")).to_have_text("Sectors: 1 selected")
    expect(page.get_by_label("Estate agent")).to_be_checked()


def test_sample_question_fills_the_box_and_ticks_its_sectors(page: Page, api: FakeApi):
    api.open()
    page.locator(".sample", has_text="proliferation typologies").click()
    expect(page.locator("#prompt-input")).to_have_value(
        "What are the key proliferation typologies facing the TCSP sector?"
    )
    expect(page.locator("#sector-summary")).to_have_text("Sectors: 2 selected")
    expect(page.get_by_label("Class 4 – Corporate services")).to_be_checked()
    expect(page.get_by_label("Class 5 – Trust services")).to_be_checked()
    expect(page.get_by_label("Estate agent")).not_to_be_checked()


def test_a_question_containing_markup_is_shown_as_text(page: Page, api: FakeApi):
    api.reply_with(answer_event())
    api.open()
    api.ask("Is <b>bold</b> & <script>alert(1)</script> ok?")
    turn = page.get_by_test_id("user-turn")
    expect(turn).to_have_text("Is <b>bold</b> & <script>alert(1)</script> ok?")
    expect(turn.locator("b, script")).to_have_count(0)


def test_server_sent_line_endings_of_either_kind_are_understood(
    page: Page, api: FakeApi
):
    api.reply_with(*BASIC_PROGRESS, answer_event())
    api.query_body = api.query_body.replace("\n", "\r\n")
    api.open()
    api.ask("Anything")
    expect(page.get_by_test_id("assistant-turn")).to_be_visible()
    expect(page.get_by_test_id("citation")).to_have_count(1)


# ---- citations -------------------------------------------------------------


def test_https_citation_is_a_link_that_opens_safely_in_a_new_tab(
    page: Page, api: FakeApi
):
    api.reply_with(answer_event(citations=[citation()]))
    api.open()
    api.ask("Anything")
    card = page.get_by_test_id("citation")
    expect(card).to_have_js_property("tagName", "A")
    expect(card).to_have_attribute("href", "https://www.iomfsa.im/code.pdf")
    expect(card).to_have_attribute("target", "_blank")
    expect(card).to_have_attribute("rel", "noopener noreferrer")


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(document.domain)",
        "http://www.iomfsa.im/code.pdf",
        "data:text/html,<script>alert(1)</script>",
        "not a url",
        "",
    ],
)
def test_citation_without_an_https_url_is_a_plain_card_not_a_link(
    page: Page, api: FakeApi, url: str
):
    api.reply_with(answer_event(citations=[citation(url=url)]))
    api.open()
    api.ask("Anything")
    card = page.get_by_test_id("citation")
    expect(card).to_have_js_property("tagName", "DIV")
    assert card.get_attribute("href") is None


def test_citation_titles_in_capitals_are_tidied_but_normal_case_is_left_alone(
    page: Page, api: FakeApi
):
    api.reply_with(
        answer_event(
            citations=[
                citation(
                    document="THE AML/CFT CODE 2019",
                    headers=["PART II - CUSTOMER DUE DILIGENCE", "Enhanced measures"],
                )
            ]
        )
    )
    api.open()
    api.ask("Anything")
    card = page.get_by_test_id("citation")
    expect(card.locator(".citation-doc")).to_have_text("The AML/CFT Code 2019")
    expect(card.locator(".crumb-first")).to_have_text(
        "Part II - Customer Due Diligence"
    )
    expect(card.locator(".crumb-rest")).to_have_text("Enhanced measures")


def test_citations_can_be_hidden_and_shown(page: Page, api: FakeApi):
    api.reply_with(answer_event())
    api.open()
    api.ask("Anything")
    panel = page.locator("#right-panel")
    button = page.locator("#toggle-citations")
    expect(panel).to_be_visible()
    button.click()
    expect(panel).to_be_hidden()
    expect(button).to_have_text("Show citations")
    button.click()
    expect(panel).to_be_visible()
    expect(button).to_have_text("Hide citations")


# ---- failures --------------------------------------------------------------


def test_an_error_event_shows_a_message_and_puts_the_question_back(
    page: Page, api: FakeApi
):
    api.reply_with(*BASIC_PROGRESS, ("error", "query failed"))
    api.open()
    api.ask("A question worth keeping")
    expect(page.get_by_test_id("error")).to_contain_text("That request didn't complete")
    expect(page.locator("#prompt-input")).to_have_value("A question worth keeping")
    expect(page.locator("#prompt-form button[type=submit]")).to_be_enabled()
    expect(page.locator("#reset-button")).to_be_enabled()
    # how far the agent got stays visible, marked as failed
    progress = page.get_by_test_id("progress")
    expect(progress.locator(".progress-label")).to_have_text(
        "Query failed · 1 search, 1 section read"
    )
    expect(progress).to_have_class(re.compile(r"\bfailed\b"))


def test_a_server_error_status_shows_the_same_message(page: Page, api: FakeApi):
    api.reply_with(status=500)
    api.open()
    api.ask("Anything")
    expect(page.get_by_test_id("error")).to_contain_text("That request didn't complete")
    expect(page.locator("#prompt-input")).to_have_value("Anything")


def test_a_reply_that_ends_without_an_answer_is_treated_as_a_failure(
    page: Page, api: FakeApi
):
    api.reply_with(*BASIC_PROGRESS)
    api.open()
    api.ask("Anything")
    expect(page.get_by_test_id("error")).to_contain_text("That request didn't complete")
    expect(page.get_by_test_id("assistant-turn")).to_have_count(0)


# ---- reset -----------------------------------------------------------------


def test_reset_clears_the_server_session_and_the_page(page: Page, api: FakeApi):
    api.reply_with(answer_event())
    api.open()
    api.ask("Anything")
    expect(page.get_by_test_id("citation")).to_have_count(1)
    resets_before = len(api.resets)

    page.locator("#reset-button").click()

    expect(page.get_by_test_id("citation")).to_have_count(0)
    expect(page.get_by_test_id("user-turn")).to_have_count(0)
    expect(page.locator("#welcome")).to_be_visible()
    assert len(api.resets) == resets_before + 1
    assert api.resets[-1]["session_id"] == page.evaluate(
        "localStorage.getItem('session_id')"
    )


def test_a_second_question_keeps_the_first_on_the_page(page: Page, api: FakeApi):
    api.reply_with(answer_event("First answer."))
    api.open()
    api.ask("First question")
    expect(page.get_by_test_id("assistant-turn")).to_have_text("First answer.")
    api.reply_with(answer_event("Second answer."))
    api.ask("Second question")
    expect(page.get_by_test_id("assistant-turn")).to_have_count(2)
    expect(page.get_by_test_id("user-turn")).to_have_text(
        ["First question", "Second question"]
    )


# ---- safety ----------------------------------------------------------------


@pytest.mark.xfail(
    strict=True,
    reason=(
        "known gap: web/app.js puts marked.parse(answer) into innerHTML with no "
        "sanitiser, so HTML in an answer runs. Remove this marker once the answer "
        "is sanitised (for example with DOMPurify) and this test passes."
    ),
)
def test_html_in_an_answer_does_not_run(page: Page, api: FakeApi):
    api.reply_with(
        answer_event(
            'Look: <img src="x" onerror="window.__ran = true"> and '
            "<script>window.__ran = true</script>"
        )
    )
    api.open()
    api.ask("Anything")
    expect(page.get_by_test_id("assistant-turn")).to_be_visible()
    page.wait_for_timeout(300)  # an onerror handler fires as soon as the image fails
    assert page.evaluate("window.__ran === true") is False


def test_html_in_a_citation_is_shown_as_text(page: Page, api: FakeApi):
    markup = '<img src="x" onerror="window.__ran = true">'
    api.reply_with(
        answer_event(
            citations=[citation(document=markup, headers=[markup], relevance=markup)]
        )
    )
    api.open()
    api.ask("Anything")
    card = page.get_by_test_id("citation")
    expect(card).to_contain_text(markup)
    expect(card.locator("img")).to_have_count(0)
    page.wait_for_timeout(300)
    assert page.evaluate("window.__ran === true") is False


# ---- small screens ---------------------------------------------------------


def test_nothing_forces_sideways_scrolling_on_a_phone(page: Page, api: FakeApi):
    wide_table = (
        "| Requirement | Detail | Reference | Notes |\n"
        "| --- | --- | --- | --- |\n"
        "| Customer due diligence measures | Identify and verify the customer | "
        "Paragraph 12 of the Code | Applies to every business relationship |\n"
    )
    long_word = "x" * 200
    page.set_viewport_size({"width": 375, "height": 700})
    api.reply_with(answer_event(f"{wide_table}\n{long_word}"))
    api.open()
    api.ask("Anything")
    expect(page.get_by_test_id("assistant-turn")).to_be_visible()
    overflow = page.evaluate(
        "document.documentElement.scrollWidth - document.documentElement.clientWidth"
    )
    assert overflow <= 0, f"page is [{overflow}]px wider than the screen"


def test_citations_start_hidden_on_a_phone_and_can_be_shown(page: Page, api: FakeApi):
    page.set_viewport_size({"width": 375, "height": 700})
    api.reply_with(answer_event())
    api.open()
    expect(page.locator("#toggle-citations")).to_have_text("Show citations")
    api.ask("Anything")
    expect(page.locator("#right-panel")).to_be_hidden()
    page.locator("#toggle-citations").click()
    expect(page.get_by_test_id("citation")).to_be_visible()
