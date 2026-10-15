import os
from functools import lru_cache

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()


def foundry_configured() -> bool:
    return bool(os.getenv("FOUNDRY_PROJECT_ENDPOINT"))


@lru_cache
def _project() -> AIProjectClient:
    return AIProjectClient(
        endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        credential=DefaultAzureCredential(),
    )


@lru_cache
def _openai():
    return _project().get_openai_client()


_registered: set[str] = set()


def ensure_agent(name: str, model: str, instructions: str) -> None:
    """Registers a new agent version once per process."""
    if name in _registered:
        return
    _project().agents.create_version(
        agent_name=name,
        definition=PromptAgentDefinition(model=model, instructions=instructions),
    )
    _registered.add(name)


def run_agent(name: str, text: str) -> str:
    """Blocking call. Wrap in asyncio.to_thread from async code."""
    resp = _openai().responses.create(
        input=text,
        extra_body={"agent_reference": {"name": name, "type": "agent_reference"}},
    )
    return resp.output_text