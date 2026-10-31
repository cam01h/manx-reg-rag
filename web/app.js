/* 1. Elements
   ========================================================================== */

const form = document.getElementById("prompt-form");
const input = document.getElementById("prompt-input");
const response = document.getElementById("response");
const citations = document.getElementById("citations");
const sendButton = form.querySelector("button[type='submit']");
const resetButton = document.getElementById("reset-button");
const toggleButton = document.getElementById("toggle-citations");
const sectorPicker = document.getElementById("sector-picker");
const sectorSummary = document.getElementById("sector-summary");
const sectorOptions = document.getElementById("sector-options");
const sectorClear = document.getElementById("sector-clear");


/* 2. State
   ========================================================================== */

let history = [];
let isQuerying = false;
let pendingBlock = null;
let pendingStatus = null;
let pendingBox = null;
let pendingLog = null;
let progressLog = [];
let documents = null;      // from GET /documents; null if it couldn't be loaded
let sectorLabels = {};     // from GET /sectors: { class_1: "Class 1 – Deposit taking", ... }

const isMobile = window.matchMedia("(max-width: 768px)");


/* 3. Session
   Held in localStorage so a refresh keeps the server-side conversation.
   ========================================================================== */

let sessionId = localStorage.getItem("session_id");
if (!sessionId) {
    sessionId =
        typeof crypto.randomUUID === "function"
            ? crypto.randomUUID()
            : "session-" + Math.random().toString(36).slice(2) + Date.now().toString(36);
    localStorage.setItem("session_id", sessionId);
}


/* 4. Rendering
   ========================================================================== */

function renderConversation() {
    response.innerHTML = "";
    for (const turn of history) {
        const block = document.createElement("div");
        block.className = "turn";

        // textContent, not innerHTML — a question containing < or &
        // would otherwise render as broken markup.
        const userTurn = document.createElement("div");
        userTurn.className = "user-turn";
        userTurn.textContent = turn.prompt;

        const assistantTurn = document.createElement("div");
        assistantTurn.className = "assistant-turn";
        assistantTurn.innerHTML = marked.parse(turn.answer);
        // every new answer redraws the whole conversation, so only the
        // newest one gets the fade-in or the older ones would replay it too
        if (turn === history[history.length - 1]) {
            assistantTurn.classList.add("enter");
        }

        assistantTurn.querySelectorAll("table").forEach((table) => {
            const wrap = document.createElement("div");
            wrap.className = "table-wrap";
            table.before(wrap);
            wrap.appendChild(table);
        });

        // The agent's progress lines, kept from when the answer was streaming.
        // Stays collapsed unless the person opened it (remembered across
        // re-renders, since every new answer redraws the whole conversation).
        const parts = [userTurn];
        if (turn.log && turn.log.length > 0) {
            const progress = buildProgressBox("done", finishedLabel("done", turn.log), turn.log);
            progress.box.open = Boolean(turn.open);
            progress.box.addEventListener("toggle", () => {
                turn.open = progress.box.open;
            });
            parts.push(progress.box);
        }
        parts.push(assistantTurn);

        block.append(...parts);
        response.appendChild(block);
    }
    response.scrollTop = response.scrollHeight;
}

function renderCitations(items) {
    citations.innerHTML = "";
    for (const [index, citation] of items.entries()) {
        const card = document.createElement("div");
        card.className = "citation-card";
        card.style.setProperty("--i", index); // style.css staggers the fade-in by this

        const id = document.createElement("div");
        id.className = "citation-id";
        id.textContent = citation.chunk_id;

        const relevance = document.createElement("div");
        relevance.className = "citation-relevance";
        relevance.textContent = citation.relevance;

        card.append(id, relevance);
        citations.appendChild(card);
    }
}

function renderError(message) {
    const block = document.createElement("div");
    block.className = "turn";
    block.textContent = message;
    response.appendChild(block);
    response.scrollTop = response.scrollHeight;
}

/* Progress box
   One expandable <details> element per question. Its <summary> is the one line
   you always see; the list inside is every progress line the server sent.
   While the agent works it shows the latest line. Once the answer lands it
   becomes "Query complete · 3 searches, 12 sections read" and stays clickable.
   The three states ("running", "done", "failed") are just a class on the box;
   style.css decides what each one looks like.
   ========================================================================== */

/* Tidying titles
   The rule is: only touch text that is entirely in capitals, which is how some
   headers come out of the documents ("PART 4 - CUSTOMER DUE DILIGENCE"). Those
   become "Part 4 - Customer Due Diligence". Anything already in normal case,
   like "The AML/CFT Code 2019", is left exactly as it is. */

// kept in capitals even inside a tidied title
const ACRONYMS = new Map(
    ["AML", "CFT", "ML", "FT", "TF", "PF", "TCSP", "VASP", "PEP", "MLRO", "FIU", "CDD",
     "EDD", "FATF", "BRA", "CRA", "SAR", "KYC", "NRA", "UK", "IOM", "FSA", "POCA", "ATCA",
     "DBROA", "RAO", "SOF", "SOW", "EU", "UN"].map((word) => [word, word])
);
ACRONYMS.set("PEPS", "PEPs");

// kept in lower case in the middle of a title
const SMALL_WORDS = new Set(["a", "an", "and", "as", "at", "but", "by", "for", "from",
                             "in", "of", "on", "or", "the", "to", "with"]);

// Roman numerals up to 39 (PART II, SCHEDULE IV). Kept narrow on purpose so
// that words like CIVIL or MIX are not mistaken for numerals.
const ROMAN_NUMERAL = /^(I{1,3}|IV|VI{0,3}|IX|X{1,3})$/;

function tidyTitle(text) {
    const isAllCaps = /[A-Z]/.test(text) && text === text.toUpperCase();
    if (!isAllCaps) return text;

    let isFirstWord = true;
    return text.replace(/[A-Za-z0-9][A-Za-z0-9']*/g, (word) => {
        const atStart = isFirstWord;
        isFirstWord = false;

        if (/\d/.test(word)) return word; // 14, 3.8.13, FSA08 ...
        const upper = word.toUpperCase();
        if (ACRONYMS.has(upper)) return ACRONYMS.get(upper);
        if (ROMAN_NUMERAL.test(upper)) return upper;

        const lower = word.toLowerCase();
        if (!atStart && SMALL_WORDS.has(lower)) return lower;
        return lower[0].toUpperCase() + lower.slice(1);
    });
}

// A "read" line arrives as a document plus one string of headers joined by
// ", ". Returns the tidied headers as a list, outermost first.
function headerTrail(entry) {
    return entry.headers
        .split(", ")
        .map((header) => header.trim())
        .filter(Boolean)
        .map(tidyTitle);
}

// The single line shown in the pill while the agent works.
function liveLabel(entry) {
    if (entry.kind === "search") return `Searching: ${entry.term}`;
    const [firstHeader] = headerTrail(entry);
    const where = [tidyTitle(entry.document), firstHeader].filter(Boolean).join(" › ");
    return `Reading: ${where}`;
}

function summariseLog(log) {
    const searches = log.filter((entry) => entry.kind === "search").length;
    const reads = log.filter((entry) => entry.kind === "read").length;
    const parts = [];
    if (searches > 0) parts.push(searches === 1 ? "1 search" : `${searches} searches`);
    if (reads > 0) parts.push(reads === 1 ? "1 section read" : `${reads} sections read`);
    return parts.join(", ");
}

function finishedLabel(state, log) {
    const verb = state === "failed" ? "Query failed" : "Query complete";
    const counts = summariseLog(log);
    return counts ? `${verb} · ${counts}` : verb;
}

function span(className, text) {
    const element = document.createElement("span");
    element.className = className;
    element.textContent = text;
    return element;
}

// One row of the expanded list. A search reads "Searching  <term>". A read is
// a breadcrumb: document (bold) › first header › the deeper headers (dim).
function appendLogItem(list, entry) {
    const item = document.createElement("li");
    item.className = entry.kind;

    if (entry.kind === "search") {
        item.append(span("log-label", "Searching"), span("log-term", entry.term));
    } else {
        item.append(span("crumb-doc", tidyTitle(entry.document)));
        headerTrail(entry).forEach((header, index) => {
            const separator = span("crumb-sep", "›");
            separator.setAttribute("aria-hidden", "true");
            item.append(separator, span(index === 0 ? "crumb-first" : "crumb-rest", header));
        });
    }
    list.appendChild(item);
}

function buildProgressBox(state, label, log) {
    const box = document.createElement("details");
    box.className = `progress ${state}`;

    const summary = document.createElement("summary");
    const dot = document.createElement("span");
    dot.className = "progress-dot";
    const text = document.createElement("span");
    text.className = "progress-label";
    text.textContent = label;
    summary.append(dot, text);

    const list = document.createElement("ul");
    list.className = "progress-log";
    for (const entry of log) {
        appendLogItem(list, entry);
    }

    box.append(summary, list);
    return { box, text, list };
}

// Called for each progress event: updates the visible line and the list,
// and keeps a copy so it can be saved with the answer.
// entry is { kind: "search", term } or { kind: "read", document, headers }.
function addProgress(entry) {
    progressLog.push(entry);
    if (pendingStatus) pendingStatus.textContent = liveLabel(entry);
    if (pendingLog) {
        appendLogItem(pendingLog, entry);
        pendingLog.scrollTop = pendingLog.scrollHeight;
    }
    response.scrollTop = response.scrollHeight;
}

/* Shows the question immediately, then the server's progress lines as they
   arrive, so the wait reads as the tool working rather than the page having
   died. Queries take roughly 40 seconds; without this people assume it's
   broken and send again, and every resend is another full agent run. */
function startPending(prompt) {
    isQuerying = true;
    sendButton.disabled = true;
    resetButton.disabled = true;
    // style.css moves the background glow only while this class is on
    document.body.classList.add("querying");

    clearWelcome();

    pendingBlock = document.createElement("div");
    pendingBlock.className = "turn enter";

    const userTurn = document.createElement("div");
    userTurn.className = "user-turn";
    userTurn.textContent = prompt;

    progressLog = [];
    const progress = buildProgressBox("running", "Searching the legislation…", []);
    pendingBox = progress.box;
    pendingStatus = progress.text;
    pendingLog = progress.list;

    pendingBlock.append(userTurn, progress.box);
    response.appendChild(pendingBlock);
    response.scrollTop = response.scrollHeight;
}

// keepBlock: leave the question and progress box on the page (used on failure).
function stopPending(keepBlock = false) {
    isQuerying = false;
    sendButton.disabled = false;
    resetButton.disabled = false;
    document.body.classList.remove("querying");

    pendingStatus = null;
    pendingBox = null;
    pendingLog = null;

    if (pendingBlock) {
        if (!keepBlock) pendingBlock.remove();
        pendingBlock = null;
    }
}

// On failure, keep the progress box if the agent got anywhere, so you can see
// how far it got. With nothing to show, remove it as before.
function failPending() {
    if (pendingBox && progressLog.length > 0) {
        pendingBox.classList.replace("running", "failed");
        pendingStatus.textContent = finishedLabel("failed", progressLog);
        stopPending(true);
    } else {
        stopPending();
    }
}


/* Reading the server's streamed reply
   /query sends a series of events, each a few lines of text like:
       event: search
       data: {"term": "customer due diligence"}
   followed by a blank line. The events are "search", "read", then "answer"
   (or "error"). This reads the reply as it arrives and calls
   onEvent(name, payload) once per event, with the payload already decoded.
   (The browser's EventSource can't be used here because /query is a POST.)
   ========================================================================== */

function parseEvent(block) {
    let name = "message";
    const dataLines = [];
    for (const line of block.split("\n")) {
        if (line.startsWith("event:")) {
            name = line.slice(6).trim();
        } else if (line.startsWith("data:")) {
            dataLines.push(line.slice(5).replace(/^ /, ""));
        }
        // anything else (comments starting with ":") is ignored
    }
    if (dataLines.length === 0) return null;
    const text = dataLines.join("\n");
    try {
        return { name, payload: JSON.parse(text) };
    } catch {
        return { name, payload: text };
    }
}

async function readEvents(reply, onEvent) {
    const reader = reply.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            buffer = buffer.replace(/\r\n/g, "\n");

            let end;
            while ((end = buffer.indexOf("\n\n")) !== -1) {
                const event = parseEvent(buffer.slice(0, end));
                buffer = buffer.slice(end + 2);
                if (event) onEvent(event.name, event.payload);
            }
        }
    } finally {
        reader.cancel().catch(() => {});
    }
}


/* 5. Query
   ========================================================================== */

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (isQuerying) return;

    const prompt = input.value;
    if (!prompt.trim()) return;

    input.value = "";
    resetInputHeight();
    sectorPicker.open = false;
    startPending(prompt);

    try {
        const reply = await fetch("/query", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                prompt,
                session_id: sessionId,
                sectors: selectedSectors()
            })
        });

        if (!reply.ok) {
            throw new Error(`server responded with status ${reply.status}`);
        }

        let data = null;
        await readEvents(reply, (name, payload) => {
            if (name === "search") {
                addProgress({ kind: "search", term: payload.term });
            } else if (name === "read") {
                addProgress({ kind: "read", document: payload.document, headers: payload.headers });
            } else if (name === "answer") {
                data = payload;
            } else if (name === "error") {
                throw new Error(`server reported an error: ${payload}`);
            }
        });
        if (!data) {
            throw new Error("the reply ended without an answer");
        }

        const log = progressLog;
        stopPending();
        history.push({ prompt, answer: data.answer, log });
        renderConversation();
        renderCitations(data.citations);
    } catch (err) {
        console.error("query failed:", err);
        failPending();
        renderError(
            "That request didn't complete. The server may still be working on it — " +
            "wait a moment before sending again."
        );
        input.value = prompt; // put the question back so it isn't lost
    }
});


/* 6. Reset
   ========================================================================== */

function clearServerSession() {
    return fetch("/reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: "", session_id: sessionId })
    });
}

resetButton.addEventListener("click", async () => {
    if (isQuerying) return;

    await clearServerSession();
    history = [];
    response.innerHTML = "";
    citations.innerHTML = "";
    input.value = "";
    resetInputHeight();
    renderWelcome();
});

// Server keeps history keyed by email; the page doesn't. Clear the server
// side on load so both start empty and a refresh means a fresh start.
clearServerSession();

/* 7. Citations toggle
   One class on <body>; the stylesheet decides what it means at each width.
   Desktop: hides the citations panel. Mobile: swaps which panel is shown.
   ========================================================================== */

function setCitationsHidden(hidden) {
    document.body.classList.toggle("citations-hidden", hidden);
    toggleButton.textContent = hidden ? "Show citations" : "Hide citations";
}

// Opens collapsed on phones, expanded on desktop.
setCitationsHidden(isMobile.matches);

toggleButton.addEventListener("click", () => {
    setCitationsHidden(!document.body.classList.contains("citations-hidden"));
});


/* 8. Textarea behaviour
   Grows with the content up to the max-height set in CSS, then scrolls.
   ========================================================================== */

function resetInputHeight() {
    input.style.height = "auto";
}

input.addEventListener("input", () => {
    input.style.height = "auto";
    input.style.height = input.scrollHeight + "px";
});

// Enter sends, Shift+Enter starts a new line.
input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        form.requestSubmit();
    }
});


/* 9. Sector picker
   The list comes from GET /sectors, so the server owns the vocabulary and the
   labels; this only draws a checkbox per entry. Ticked values go out with each
   query as `sectors`. Nothing ticked means no filter: search everything.
   The selection is remembered in localStorage, like the session id.
   ========================================================================== */

const SECTORS_KEY = "sectors";

function loadSavedSectors() {
    try {
        const saved = JSON.parse(localStorage.getItem(SECTORS_KEY) || "[]");
        return Array.isArray(saved) ? saved : [];
    } catch {
        return [];
    }
}

function saveSectors(values) {
    try {
        localStorage.setItem(SECTORS_KEY, JSON.stringify(values));
    } catch {
        // private browsing or blocked storage: the picker still works,
        // it just won't be remembered next visit
    }
}

// Read from the boxes on the page rather than from storage, so a saved value
// the server no longer offers can never be sent (it would get a 422).
function selectedSectors() {
    return Array.from(
        sectorOptions.querySelectorAll("input[type='checkbox']:checked"),
        (box) => box.value
    );
}

// Used by the sample questions: ticks exactly these sectors and unticks the rest.
function setSelectedSectors(values) {
    const boxes = sectorOptions.querySelectorAll("input[type='checkbox']");
    if (boxes.length === 0) return; // the sector list didn't load; leave things alone
    for (const box of boxes) {
        box.checked = values.includes(box.value);
    }
    saveSectors(selectedSectors());
    updateSectorSummary();
}

function updateSectorSummary() {
    const count = selectedSectors().length;
    sectorSummary.textContent = count === 0 ? "Sectors: all" : `Sectors: ${count} selected`;
    sectorPicker.classList.toggle("has-selection", count > 0);
}

async function loadSectors() {
    try {
        const reply = await fetch("/sectors");
        if (!reply.ok) {
            throw new Error(`server responded with status ${reply.status}`);
        }
        const labels = await reply.json();
        sectorLabels = labels;
        const saved = new Set(loadSavedSectors());

        for (const [value, label] of Object.entries(labels)) {
            const row = document.createElement("label");
            row.className = "sector-option";

            const box = document.createElement("input");
            box.type = "checkbox";
            box.value = value;
            box.checked = saved.has(value);

            const text = document.createElement("span");
            text.textContent = label;

            row.append(box, text);
            sectorOptions.appendChild(row);
        }
    } catch (err) {
        console.error("loading sectors failed:", err);
        sectorOptions.textContent =
            "Couldn't load the sector list. Questions will search everything.";
        sectorClear.hidden = true;
    }
    updateSectorSummary();
}

sectorOptions.addEventListener("change", () => {
    saveSectors(selectedSectors());
    updateSectorSummary();
});

sectorClear.addEventListener("click", () => {
    for (const box of sectorOptions.querySelectorAll("input[type='checkbox']")) {
        box.checked = false;
    }
    saveSectors([]);
    updateSectorSummary();
});

// Close the panel on a click anywhere else, or on Escape.
document.addEventListener("click", (event) => {
    if (sectorPicker.open && !sectorPicker.contains(event.target)) {
        sectorPicker.open = false;
    }
});

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && sectorPicker.open) {
        sectorPicker.open = false;
        sectorSummary.focus();
    }
});


/* 10. Welcome screen
   Shown when the page is empty (on load, and after Reset): what the tool is,
   which documents it has, what the Sectors button does, and a few questions to
   try. It disappears when the first question is sent.
   ========================================================================== */

// Each sample ticks its own sectors (or none) and fills the question box.
const SAMPLE_QUESTIONS = [
    {
        text: "What's the difference between source of funds and source of wealth?",
        sectors: []
    },
    {
        text: "What are the governance requirements in the rule book for a bank?",
        sectors: ["class_1"]
    },
    {
        text: "What are the key proliferation typologies facing the TCSP sector?",
        sectors: ["class_4", "class_5"]
    }
];

// Plain-English names for the documents' legal standing, in reading order.
const DOCUMENT_GROUPS = [
    { hierarchy: "Primary legislation", title: "Acts of Tynwald" },
    { hierarchy: "Secondary legislation", title: "Regulations, Orders and Codes" },
    { hierarchy: "Guidance", title: "Guidance" },
    { hierarchy: "Supplemental", title: "Supporting documents" }
];

async function loadDocuments() {
    try {
        const reply = await fetch("/documents");
        if (!reply.ok) {
            throw new Error(`server responded with status ${reply.status}`);
        }
        documents = await reply.json();
    } catch (err) {
        console.error("loading documents failed:", err);
        documents = null; // the welcome screen just leaves the list out
    }
}

function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
}

function buildDocumentList() {
    const box = element("details", "welcome-docs");
    const summary = element("summary");
    summary.append(
        span("welcome-docs-count", `${documents.length} documents`),
        span("welcome-docs-loaded", "loaded"),
        span("welcome-docs-hint", "· see what's included")
    );

    const body = element("div", "welcome-docs-body");
    const known = new Set(DOCUMENT_GROUPS.map((group) => group.hierarchy));
    const groups = [...DOCUMENT_GROUPS];
    for (const doc of documents) {
        if (!known.has(doc.hierarchy)) {
            known.add(doc.hierarchy);
            groups.push({ hierarchy: doc.hierarchy, title: doc.hierarchy });
        }
    }
    for (const group of groups) {
        const names = documents.filter((doc) => doc.hierarchy === group.hierarchy);
        if (names.length === 0) continue;
        body.append(element("h3", "", `${group.title} (${names.length})`));
        const list = element("ul");
        for (const doc of names) {
            list.append(element("li", "", doc.name));
        }
        body.append(list);
    }

    box.append(summary, body);
    return box;
}

function sampleNote(sample) {
    if (sample.sectors.length === 0) return "Searches everything";
    return "Sectors: " + sample.sectors.map((key) => sectorLabels[key] || key).join(", ");
}

function useSample(sample) {
    setSelectedSectors(sample.sectors);
    input.value = sample.text;
    input.dispatchEvent(new Event("input")); // grows the box to fit
    input.focus();

    // a brief highlight so it's clear the Sectors button just changed
    sectorPicker.classList.remove("flash");
    void sectorPicker.offsetWidth; // lets the animation restart if it is clicked twice
    sectorPicker.classList.add("flash");
}

function renderWelcome() {
    clearWelcome();
    if (history.length > 0 || isQuerying) return;

    const welcome = element("div", "welcome");
    welcome.id = "welcome";

    welcome.append(
        element("p", "welcome-kicker", "Isle of Man · AML/CFT"),
        element("h2", "", "Ask a question about Isle of Man AML/CFT rules"),
        element("p", "welcome-intro",
            "Answers come from the actual laws and guidance, not general knowledge, and every " +
            "answer shows where in the documents it came from. If the documents don't cover " +
            "your question, it will tell you rather than guess.")
    );

    if (documents && documents.length > 0) {
        welcome.append(buildDocumentList());
    }

    const tip = element("div", "welcome-tip");
    tip.append(
        element("strong", "", "Focus on your business. "),
        "Use ", element("em", "", "Sectors"),
        " at the top right to say what kind of business you are, for example a bank or a trust " +
        "company, and the answers will focus on the rules that apply to you. Leave it blank to " +
        "search everything."
    );
    welcome.append(tip);

    welcome.append(element("h3", "welcome-try", "Try one of these"));
    const samples = element("div", "welcome-samples");
    for (const sample of SAMPLE_QUESTIONS) {
        const button = element("button", "sample");
        button.type = "button";
        const noteClass = sample.sectors.length > 0 ? "sample-note filtered" : "sample-note";
        button.append(span("sample-text", sample.text), span(noteClass, sampleNote(sample)));
        button.addEventListener("click", () => useSample(sample));
        samples.append(button);
    }
    welcome.append(samples);

    response.prepend(welcome);
}

function clearWelcome() {
    const welcome = document.getElementById("welcome");
    if (welcome) welcome.remove();
}

Promise.all([loadSectors(), loadDocuments()]).then(renderWelcome);
