"""
LLM clients and provider resolution.

Backends:
  - xai / anthropic — cloud (existing)
  - ollama — local OpenAI-compatible endpoint (Pi or Stronghold LAN)
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from dotenv import load_dotenv

from ..core import Config, LogBase


class LLMClient(ABC):
    """Interface all AMI LLM clients conform to."""

    @abstractmethod
    def generate_response(self, prompt: str, temperature: float = 0.7, max_tokens: int = 100, **kwargs) -> str:
        pass


class XAIClient(LLMClient, LogBase):
    """xAI API client (OpenAI-compatible)."""

    def __init__(self, api_key: str, model: str = "grok-3-mini"):
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
        self.model = model

    def get_completion(self, content: str | List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 100, **kwargs):
        if isinstance(content, str):
            messages: List[Dict[str, str]] = [{"role": "user", "content": content}]
        elif isinstance(content, list):
            messages = content
        else:
            raise ValueError(f"XAIClient.get_completion: content arg invalid. {content}")

        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_completion_tokens=max_tokens,
            **kwargs,
        )

    def tool_call(self, prompt: str, tools):
        messages = [{"role": "user", "content": "system_prompt"}, {"role": "user", "content": prompt}]
        tools_definition = [(tool.name, tool.description, tool.arg_schema) for tool in tools]
        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools_definition,
            tool_choice="auto",
        )

    def custom_tool_call(self, messages: List[Dict[str, str]], stop="obervation"):
        return self.get_completion(messages, temperature=0.0, max_tokens=350).choices[0].message.content.strip()

    def generate_response(self, prompt: str, **kwargs) -> str:
        result = self.get_completion(prompt, **kwargs).choices[0].message
        self.logs.debug(f"XAI generate completion called. Raw output: {result}")
        return result.content.strip()


class AnthropicClient(LLMClient, LogBase):
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        from anthropic import Anthropic

        self.client = Anthropic(api_key=api_key)
        self.model = model

    def get_completion(self, prompt: str, temperature: float = 0.7, max_tokens: int = 100, **kwargs):
        return self.client.messages.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    def generate_response(self, prompt: str, **kwargs) -> str:
        response = self.get_completion(prompt, **kwargs)
        return response.content[0].text.strip()


class OllamaClient(LLMClient, LogBase):
    """
    Local / LAN Ollama via OpenAI-compatible HTTP (no ollama pip package required).

    Default base: http://127.0.0.1:11434/v1
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434/v1",
        model: str = "llama3.2:1b",
        api_key: str = "ollama",
        timeout_sec: float = 120.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout_sec = timeout_sec

    def _chat(self, messages: List[Dict[str, str]], temperature: float, max_tokens: int) -> str:
        url = f"{self.base_url}/chat/completions"
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Ollama unreachable at {self.base_url} ({exc}). "
                "Start ollama or set llm.backend to xai/anthropic."
            ) from exc
        try:
            return payload["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Unexpected Ollama response shape: {payload!r}") from exc

    def generate_response(self, prompt: str, temperature: float = 0.7, max_tokens: int = 100, **kwargs) -> str:
        messages = [{"role": "user", "content": prompt}]
        return self._chat(messages, temperature=temperature, max_tokens=max_tokens)

    def custom_tool_call(self, messages: List[Dict[str, str]], stop="obervation"):
        return self._chat(messages, temperature=0.0, max_tokens=350)


def _load_dotenv_if_present() -> None:
    env_path = Config().environment_file
    if env_path.is_file():
        load_dotenv(env_path)


def resolve_llm_client(
    backend: Optional[str] = None,
    *,
    ollama_base_url: Optional[str] = None,
    ollama_model: Optional[str] = None,
) -> LLMClient:
    """
    Pick an LLM client.

    Priority:
      1. Explicit backend arg
      2. AMI_LLM_BACKEND env
      3. Config llm.backend if present
      4. Legacy: XAI_APIKEY / ANTHROPIC_APIKEY env (.env)
      5. Default attempt: ollama local
    """
    _load_dotenv_if_present()

    cfg = Config()
    llm_cfg = cfg.get("llm", {}) or {}
    name = (
        backend
        or os.environ.get("AMI_LLM_BACKEND")
        or llm_cfg.get("backend")
        or ""
    )
    name = str(name).strip().lower()

    if not name:
        if os.environ.get("XAI_APIKEY"):
            name = "xai"
        elif os.environ.get("ANTHROPIC_APIKEY"):
            name = "anthropic"
        else:
            name = "ollama"

    if name in ("ollama", "local"):
        base = (
            ollama_base_url
            or os.environ.get("AMI_OLLAMA_BASE_URL")
            or llm_cfg.get("ollama_base_url")
            or "http://127.0.0.1:11434/v1"
        )
        model = (
            ollama_model
            or os.environ.get("AMI_OLLAMA_MODEL")
            or llm_cfg.get("model")
            or "llama3.2:1b"
        )
        return OllamaClient(base_url=str(base), model=str(model))

    if name in ("xai", "grok"):
        key = os.environ.get("XAI_APIKEY") or os.environ.get("XAI_API_KEY")
        if not key:
            raise ValueError("llm.backend=xai requires XAI_APIKEY")
        model = llm_cfg.get("model") or "grok-3-mini"
        return XAIClient(api_key=key, model=str(model))

    if name in ("anthropic", "claude"):
        key = os.environ.get("ANTHROPIC_APIKEY") or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError("llm.backend=anthropic requires ANTHROPIC_APIKEY")
        model = llm_cfg.get("model") or "claude-3-opus-20240229"
        return AnthropicClient(api_key=key, model=str(model))

    raise ValueError(f"Unknown llm backend: {name!r} (use ollama, xai, anthropic)")


class LLMProvider(LogBase):
    def __init__(self, client: LLMClient):
        super().__init__()
        self.client = client

    @classmethod
    def from_environment(cls) -> "LLMProvider":
        """Instantiate LLMProvider from env + config (ollama | xai | anthropic)."""
        client = resolve_llm_client()
        client.logs.debug(f"{client.__class__.__name__} loaded from environment/config.")
        return cls(client)

    def generate_response(self, prompt: str, **kwargs) -> str:
        return self.client.generate_response(prompt, **kwargs)

    def as_zero_shot(self) -> "ZeroShot":
        from .prompts import ZeroShot

        return ZeroShot(self.client)

    def as_think_and_plan_agent(self) -> "ThinkAndPlanAgent":
        from .agents import ThinkAndPlanAgent

        return ThinkAndPlanAgent(self.client)

    def as_react_agent(self, headspace_name: str) -> "ReActAgent":
        from .agents import ReActAgent

        return ReActAgent(self.client, headspace_name)

    def as_funccalling_toa_agent(self, headspace_name: str):
        from .agents import FunctionCallingThoughActionObservation

        return FunctionCallingThoughActionObservation(self.client, headspace_name)
