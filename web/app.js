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
let pendingSource = null;

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

        assistantTurn.querySelectorAll("table").forEach((table) => {
            const wrap = document.createElement("div");
            wrap.className = "table-wrap";
            table.before(wrap);
            wrap.appendChild(table);
        });

        block.append(userTurn, assistantTurn);
        response.appendChild(block);
    }
    response.scrollTop = response.scrollHeight;
}

function renderCitations(items) {
    citations.innerHTML = "";
    for (const citation of items) {
        const card = document.createElement("div");
        card.className = "citation-card";

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

/* Shows the question immediately with a live counter, so the wait reads as
   the tool working rather than the page having died. Queries take roughly
   40 seconds; without this people assume it's broken and send again, and
   every resend is another full agent run. */
function startPending(prompt) {
    isQuerying = true;
    sendButton.disabled = true;
    resetButton.disabled = true;

    pendingBlock = document.createElement("div");
    pendingBlock.className = "turn";

    const userTurn = document.createElement("div");
    userTurn.className = "user-turn";
    userTurn.textContent = prompt;

    const status = document.createElement("div");
    status.className = "pending";

    pendingBlock.append(userTurn, status);
    response.appendChild(pendingBlock);
    response.scrollTop = response.scrollHeight;

    status.textContent = "Searching the legislation…";

    pendingSource = new EventSource("/sse-updates");
    pendingSource.onmessage = (e) => {
        status.textContent = JSON.parse(e.data);
    };


}

function stopPending() {
    isQuerying = false;
    sendButton.disabled = false;
    resetButton.disabled = false;
    if (pendingSource) {
        pendingSource.close();
        pendingSource = null;
    }

    if (pendingBlock) {
        pendingBlock.remove();
        pendingBlock = null;
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

        const data = await reply.json();

        stopPending();
        history.push({ prompt, answer: data.answer });
        renderConversation();
        renderCitations(data.citations);
    } catch (err) {
        console.error("query failed:", err);
        stopPending();
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

loadSectors();
