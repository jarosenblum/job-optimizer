from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI


@dataclass
class LLMConfig:
    model: str
    temperature: float


def _load_env_once() -> None:
    """
    Load .env from the repository root deterministically.
    This prevents Streamlit working-directory issues.
    """
    repo_root = Path(__file__).resolve().parents[1]  # llm/ -> repo root
    env_path = repo_root / ".env"
    load_dotenv(dotenv_path=env_path, override=False)


def load_llm_config() -> LLMConfig:
    _load_env_once()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))
    return LLMConfig(model=model, temperature=temperature)


def get_client() -> OpenAI:
    _load_env_once()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Ensure .env exists at repo root and contains "
            "OPENAI_API_KEY=... (no quotes, no spaces)."
        )
    return OpenAI(api_key=api_key)


def chat_json(client: OpenAI, config: LLMConfig, system: str, user: str) -> str:
    resp = client.chat.completions.create(
        model=config.model,
        temperature=config.temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return resp.choices[0].message.content or ""