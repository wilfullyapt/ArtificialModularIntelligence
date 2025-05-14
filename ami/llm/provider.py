"""LLM Client for making requests to language models."""

import os
from abc import ABC, abstractmethod

from dotenv import load_dotenv
from openai import OpenAI
from anthropic import Anthropic

from ami.core import Config, LogBase

from .agents import FunctionCallingThoughActionObservation, ReActAgent, ThinkAndPlanAgent
from .prompts import ZeroShot

class LLMClient(ABC):
    """
    LLMClient is the interface for all child LLMClients to conform to.
    All agents and LLM calls by the AMI system are expecte to interface through this class
    """
    @abstractmethod
    def generate_text(self, prompt: str, temperature: float = 0.7, max_tokens: int = 100, **kwargs) -> str:
        pass

# XAI Client implementation
class XAIClient(LLMClient):
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")

    def get_completion(self, prompt: str, temperature: float = 0.7, max_tokens: int = 100, **kwargs):
        return self.client.chat.completions.create(
            model="grok-3-latest",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

#   def generate_text(self, prompt: str, temperature: float = 0.7, max_tokens: int = 100, **kwargs) -> str:
    def generate_text(self, prompt: str, **kwargs) -> str:
        response = self.get_completion(prompt, **kwargs)
#       return response.choices[0].message.content.strip()
        return response.choices[0].message

# Anthropic Client implementation
class AnthropicClient(LLMClient):
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)

    def get_completion(self, prompt: str, temperature: float = 0.7, max_tokens: int = 100, **kwargs):
        return self.client.messages.create(
            model="claude-3-opus-20240229",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

    def generate_text(self, prompt: str, **kwargs) -> str:
        response = self.get_completion(prompt, **kwargs)
        return response.content[0].text.strip()

# Main provider class
class LLMProvider(LogBase):
    def __init__(self, client: LLMClient):
        super().__init__()
        self.client = client

    @classmethod
    def from_environment(cls) -> 'LLMProvider':
        """Instantiate LLMProvider based on environment variables or .env file."""
        if "XAI_APIKEY" in os.environ:
            client = XAIClient(api_key=os.environ["XAI_APIKEY"])
        elif "ANTHROPIC_APIKEY" in os.environ:
            client = AnthropicClient(api_key=os.environ["ANTHROPIC_APIKEY"])
        else:
            env_path = Config().environment_file
            if env_path.is_file():
                load_dotenv(env_path)
                if "XAI_APIKEY" in os.environ:
                    client = XAIClient(api_key=os.environ["XAI_APIKEY"])
                    print("XAI Client loaded from environment")
                elif "ANTHROPIC_APIKEY" in os.environ:
                    client = AnthropicClient(api_key=os.environ["ANTHROPIC_APIKEY"])
                    print("Anthropic Client loaded from environment")
                else:
                    raise ValueError("No API keys found in .env file.")
            else:
                raise ValueError("No API keys found and .env file not present.")
        return cls(client)

    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using the underlying client."""
        return self.client.generate_text(prompt, **kwargs)

    def as_zero_shot(self) -> 'ZeroShot':
        """Return a ZeroShot instance with this provider's client."""
        return ZeroShot(self)

    def as_think_and_plan_agent(self) -> 'ThinkAndPlanAgent':
        """Return a ThinkAndPlanAgent instance."""
        return ThinkAndPlanAgent(self)

    def as_react_agent(self) -> 'ReActAgent':
        """Return a ReActAgent instance."""
        return ReActAgent(self)

    def as_funccalling_toa_agent(self):
        """ Return a function calling Thought/Action/Oberservation agent """
        return FunctionCallingThoughActionObservation(self)

