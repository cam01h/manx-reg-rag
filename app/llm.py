import asyncio
from pydantic import BaseModel
from pydantic_ai import Agent
from config import MODEL, SYSTEM_PROMPT
from db_ops.retrieval import get_chunks_with_definitions
from dotenv import load_dotenv

load_dotenv()

query = "What are the risk factors I must consider when carrying out a customer risk assessment?"


class Citation(BaseModel):
    chunk_id: str
    relevance: str


class AgentResponse(BaseModel):
    answer: str
    citations: list[Citation]


agent = Agent(
    MODEL,
    instructions=SYSTEM_PROMPT,
    output_type=AgentResponse,
    tools=[get_chunks_with_definitions],
)


async def main():
    print(f"System prompt: {SYSTEM_PROMPT}")
    print(f"Q: {query}")
    response = await agent.run(query)
    print(f"A: {response.output.answer}")
    for cit in response.output.citations:
        print("-----------------------------")
        print(cit.chunk_id)
        print(cit.relevance)
    print("==============================")


if __name__ == "__main__":
    asyncio.run(main())
