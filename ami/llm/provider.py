"""LLM Client for making requests to language models."""

import os
from abc import ABC, abstractmethod
from typing import Dict, List

from dotenv import load_dotenv
from openai import OpenAI
from anthropic import Anthropic

from ..core import Config, LogBase

from .agents import FunctionCallingThoughActionObservation, ReActAgent, ThinkAndPlanAgent
from .prompts import ZeroShot

class LLMClient(ABC):
    """
    LLMClient is the interface for all child LLMClients to conform to.
    All agents and LLM calls by the AMI system are expecte to interface through this class
    """
    @abstractmethod
    def generate_response(self, prompt: str, temperature: float = 0.7, max_tokens: int = 100, **kwargs) -> str:
        pass

class XAIClient(LLMClient, LogBase):
    """ This is an LLM Client based on the XAI API """
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
        self.model = "grok-3-mini"

    def get_completion(self, content: str|List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 100, **kwargs):
        if isinstance(content, str):
            messages: List[Dict[str, str]] = [{"role": "user", "content": content}]
        elif isinstance(content, list):
            messages: List[Dict[str, str]] = content 
        else:
            raise ValueError(f"XAIClient.get_completion: content arg invalid. {content}")

        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_completion_tokens=max_tokens,
            **kwargs
        )

    def tool_call(self, prompt: str, tools):
        messages = [{"role": "user", "content": "system_prompt"},{"role": "user", "content": prompt}]
        tools_definition = [ (tool.name, tool.description, tool.arg_schema) for tool in tools ]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools_definition,
            tool_choice="auto",
        )
        return response

    def custom_tool_call(self, messages: List[Dict[str, str]], stop="obervation"):
        return self.get_completion(messages, temperature=0.0, max_tokens=350).choices[0].message.content.strip()
        return self.get_completion(messages, temperature=0.0, max_tokens=350, stop=stop).choices[0].message.content.strip()


    def generate_response(self, prompt: str, **kwargs) -> str:
        result = self.get_completion(prompt, **kwargs).choices[0].message
        self.logs.debug(f"XAI generate completion called. Raw output: {result}")
        return result.content.strip()

class AnthropicClient(LLMClient, LogBase):
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

    def generate_response(self, prompt: str, **kwargs) -> str:
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
                
                elif "ANTHROPIC_APIKEY" in os.environ:
                    client = AnthropicClient(api_key=os.environ["ANTHROPIC_APIKEY"])
                
                else:
                    raise ValueError("No API keys found in .env file.")
            else:
                raise ValueError("No API keys found and .env file not present.")

        client.logs.debug(f"{client.__class__.__name__} loaded from environment.")
        return cls(client)

    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate text using the underlying client."""
        return self.client.generate_response(prompt, **kwargs)

    def as_zero_shot(self) -> 'ZeroShot':
        """Return a ZeroShot instance with this provider's client."""
        return ZeroShot(self.client)

    def as_think_and_plan_agent(self) -> 'ThinkAndPlanAgent':
        """Return a ThinkAndPlanAgent instance."""
        return ThinkAndPlanAgent(self.client)

    def as_react_agent(self, headspace_name: str) -> 'ReActAgent':
        """Return a ReActAgent instance."""
        return ReActAgent(self.client, headspace_name)

    def as_funccalling_toa_agent(self, headspace_name: str):
        """ Return a function calling Thought/Action/Oberservation agent """
        return FunctionCallingThoughActionObservation(self.client, headspace_name)

