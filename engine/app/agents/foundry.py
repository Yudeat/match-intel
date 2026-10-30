import os
from functools import lru_cache
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

def foundry_configured() -> bool:
    return bool(os.getenv("AZURE_OPENAI_ENDPOINT"))

@lru_cache
def _openai() -> AzureOpenAI:
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(), 
        "https://cognitiveservices.azure.com/.default"
    )
    # Ensure base endpoint lacks trailing path suffixes like /openai/v1
    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
    if endpoint.endswith("/openai/v1"):
        endpoint = endpoint[:-10]
        
    return AzureOpenAI(
        azure_ad_token_provider=token_provider,
        azure_endpoint=endpoint,
        api_version="2024-08-01-preview"
    )

def ensure_agent(name: str, model: str, instructions: str) -> None:
    pass

def run_agent(name: str, text: str, system_instruction: str = "You are a football tactical analyst. Output valid JSON.") -> str:
    response = _openai().chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content