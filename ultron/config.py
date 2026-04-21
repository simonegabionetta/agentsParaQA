"""Configuração do Ultron via .env / variáveis de ambiente."""

import os
from dataclasses import dataclass
from pathlib import Path

_DEFAULT_MODELS = {
    "anthropic": "claude-opus-4-5",
    "openai":    "gpt-4o",
    "gemini":    "gemini/gemini-1.5-pro",
    "groq":      "groq/llama-3.1-70b-versatile",
    "ollama":    "ollama/llama3",
}


@dataclass
class Config:
    llm_provider: str = "anthropic"
    llm_model: str = ""
    api_key: str = ""

    @property
    def resolved_model(self) -> str:
        return self.llm_model or _DEFAULT_MODELS.get(self.llm_provider, self.llm_provider)


def load_config() -> Config:
    _load_dotenv()
    provider = os.getenv("LLM_PROVIDER", "anthropic").strip().lower()
    model    = os.getenv("LLM_MODEL", "").strip()

    _KEY_MAP = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai":    "OPENAI_API_KEY",
        "gemini":    "GEMINI_API_KEY",
        "groq":      "GROQ_API_KEY",
        "ollama":    "",
    }
    env_var = _KEY_MAP.get(provider, "LLM_API_KEY")
    api_key = (os.getenv(env_var, "") or os.getenv("LLM_API_KEY", "")).strip()

    return Config(llm_provider=provider, llm_model=model, api_key=api_key)


def _load_dotenv():
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
