import os
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.deepseek import DeepSeekProvider
from tests.app.models import AnchorJudgement, GroundingJudgement
from agent_metrics import JUDGE_MODEL

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

judge_model = OpenAIChatModel(
    JUDGE_MODEL,
    provider=DeepSeekProvider(api_key=DEEPSEEK_API_KEY),
)

ANCHOR_PROMPT = (
    "You are assessing whether a specific piece of source material is reflected "
    "in an answer about Isle of Man AML/CFT regulation.\n"
    "\n"
    "You will receive one source extract and one answer. Decide whether the "
    "substance of the extract is conveyed in the answer.\n"
    "\n"
    "The answer will paraphrase, restructure and reorder. Judge whether the same "
    "substantive content is present, not whether the wording matches.\n"
    "\n"
    "Return True only if the specific content of the extract is conveyed. Return "
    "False if the answer merely addresses the same topic, cites the same "
    "provision, or states something related without conveying what the extract "
    "actually says.\n"
    "\n"
    "Give your reasoning in one or two sentences, then the verdict. Do not assess "
    "whether the answer is correct, complete or well written."
)

anchor_judge = Agent(
    judge_model, instructions=ANCHOR_PROMPT, output_type=AnchorJudgement
)

GROUNDING_PROMPT = (
    "You are checking whether an answer about Isle of Man AML/CFT regulation is "
    "supported by the source material it was given.\n"
    "\n"
    "You will receive a set of source extracts and one answer. Identify any "
    "substantive claim in the answer that is not supported by the extracts.\n"
    "\n"
    "A claim is unsupported if no extract states it or entails it. Correct "
    "statements that do not appear in the extracts are still unsupported — you "
    "are checking provenance, not accuracy.\n"
    "\n"
    "Ignore framing, structure, summarising sentences and practical commentary "
    "that draws together content from the extracts. Focus on assertions about "
    "what the law or guidance requires.\n"
    "\n"
    "List each unsupported claim briefly. Set grounded to True only if there are "
    "none."
)

grounding_judge = Agent(
    judge_model, instructions=GROUNDING_PROMPT, output_type=GroundingJudgement
)
