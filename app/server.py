from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from app.llm import agent

app = FastAPI()

conversation = []


class QueryRequest(BaseModel):
    prompt: str


@app.post("/query")
async def query(request: QueryRequest):
    global conversation
    result = await agent.run(request.prompt, message_history=conversation)
    conversation = result.all_messages()
    return result.output.model_dump()


@app.post("/reset")
async def reset():
    global conversation
    conversation = []
    return {"status": "ok"}


app.mount("/", StaticFiles(directory="web", html=True), name="web")
