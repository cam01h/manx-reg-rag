const form = document.getElementById("prompt-form");
const input = document.getElementById("prompt-input");
const response = document.getElementById("response");
const citations = document.getElementById("citations");
const resetButton = document.getElementById("reset-button");

let history = [];

function renderConversation() {
    response.innerHTML = "";
    for (const turn of history) {
        const block = document.createElement("div");
        block.className = "turn";
        block.innerHTML = `
            <div class="user-turn">${turn.prompt}</div>
            <div class="assistant-turn">${marked.parse(turn.answer)}</div>
        `;
        response.appendChild(block);
    }
    response.scrollTop = response.scrollHeight;
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const prompt = input.value;
    input.value = "";

    const reply = await fetch("/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt })
    });
    const data = await reply.json();

    history.push({ prompt, answer: data.answer });
    renderConversation();

    citations.innerHTML = "";
    for (const citation of data.citations) {
        const card = document.createElement("div");
        card.className = "citation-card";
        card.innerHTML = `
            <div class="citation-id">${citation.chunk_id}</div>
            <div class="citation-relevance">${citation.relevance}</div>
        `;
        citations.appendChild(card);
    }
});

resetButton.addEventListener("click", async () => {
    await fetch("/reset", { method: "POST" });
    history = [];
    response.innerHTML = "";
    citations.innerHTML = "";
    input.value = "";
});
