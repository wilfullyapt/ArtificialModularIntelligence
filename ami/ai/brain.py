""" The Brain is the meat and potatoes of the AI. Access to LLMs should be managed here """
import sys
from importlib import import_module
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, List, Literal, Optional
from functools import cached_property

from langchain_together import Together
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from pydantic import BaseModel

from ami.core import LogBase, Config, PluginRegistry
from ami.headspace import Dialog
from ami.headspace.core.calendar import prompts

HEADSPACE_ROUTER = """You are an AI router designed to responde with the approprate Headspace
to use to fulfill a user request. The HUMAN query will be passed to the approprate Headspace,
so choose carefully. It is very important you only respond with one word.

Here are some examples:

{examples}

Here is a list of your availalbe headspaces:
{headspaces}

Begin!

HUMAN: {query}
AI:
"""

HUMAN_WITH_MEMORY = """
Memory:
{memory}

Human:
{prompt}
"""

HUMAN_WITHOUT_MEMORY = """
Human:
{prompt}
"""

class AgentNotFound(Exception):
    """ Agent not found exception """
    pass

class Brain(LogBase):
    """
    The Brain class is the language processing part of the AI system, responsible for managing
    and coordinating the various Headspaces that resolve the queries with the available Headspaces.
    It acts as a router, determining the appropriate Headspace to handle a given user query, and
    facilitates the interaction between the user and the selected Headspace.
    """

    def __init__(self, process_manager: "IPCManager"):
        """ 
        Initialize the Brain instance.

        Args:
            temp_comms: Temporal communications system
            plugin_registry: Registry managing all plugins including headspaces
        """
        super().__init__()

        self.registry = PluginRegistry(process_manager)
        
        config = Config()
        self.tk = config["together_apikey"]
        self._routing_cache = {}

    def __contains__(self, value: str):
        """Check if a headspace exists."""
        return value.upper() in self.available_headspaces

    def __getitem__(self, headspace_name: str) -> 'HeadspacePlugin':
        """Get a headspace plugin by name."""
        plugin = self.plugin_registry.get_plugin(headspace_name.lower())
        if not plugin:
            self.logs.error(f"Headspace({headspace_name}) cannot be found in Brain")
            raise AgentNotFound(f"Headspace({headspace_name}) cannot be found in Brain")
        return plugin

    @cached_property
    def available_headspaces(self) -> List[str]:
        """Get list of available headspace names."""
        return [name.upper() for name in self.plugin_registry.get_plugins_by_type(PluginType.HEADSPACE)]

    def llm_spawner(self,
                    model_name="mistralai/Mistral-7B-Instruct-v0.2",
                    temperature=0,
                    top_k=1,
                    max_tokens=200):
        """Return an instance of Language Model from LangChain."""
        model_name = "meta-llama/Llama-3-8b-chat-hf"
        return Together(model=model_name,
                      temperature=temperature,
                      top_k=top_k,
                      together_api_key=self.tk,
                      max_tokens=max_tokens)

    def mixtral_llm(self, max_tokens=256):
        """Return an instance of Mixtral Language Model."""
        model = "mistralai/Mistral-7B-Instruct-v0.2"
        return Together(model=model,
                      temperature=0,
                      top_k=1,
                      max_tokens=max_tokens,
                      together_api_key=self.tk)

    def get_human_prompt(self, prompt: str, history: str="") -> str:
        """Generate a prompt string with optional conversation history."""
        if history:
            human_prompt = PromptTemplate.from_template(HUMAN_WITH_MEMORY)
            return human_prompt.format(prompt=prompt, memory=history)

        human_prompt = PromptTemplate.from_template(HUMAN_WITHOUT_MEMORY)
        return human_prompt.format(prompt=prompt)

    async def get_routing_examples(self) -> List[str]:
        """Get routing examples from all headspaces."""
        if not self._routing_cache:
            routes = []
            headspaces = await self.plugin_registry.get_plugins_by_type(PluginType.HEADSPACE)
            for name, headspace in headspaces.items():
                try:
                    hs_opt = [f"HUMAN: {route}\nAI: {name.upper()}" 
                             for route in headspace.prompts.ROUTING]
                    routes.extend(hs_opt)
                except AttributeError as e:
                    self.logs.error(f"Cannot load routing for {name}: {e}")
            self._routing_cache = routes
        return self._routing_cache

    def clear_routing_cache(self):
        """Clear the routing examples cache."""
        self._routing_cache.clear()

    async def get_headspace_from_prompt(self, query: str) -> 'HeadspacePlugin':
        """Determine the appropriate headspace for a query."""
        prompt = ChatPromptTemplate.from_template(HEADSPACE_ROUTER)
        chain = prompt | self.mixtral_llm() | StrOutputParser()

        examples = "\n\n".join(await self.get_routing_examples())
        options = str(self.available_headspaces)
        result = chain.invoke({
            "examples": examples,
            "headspaces": options, 
            "query": query
        })
        headspace_name = result.strip().split()[0]

        return await self[headspace_name]

    async def query(self, prompt: str, history: str="", load_msg_callback=None) -> Dialog:
        """
        Process a query using the appropriate headspace.

        Args:
            prompt: The user's input query
            history: Optional conversation history
            load_msg_callback: Optional callback for progress updates

        Returns:
            Dialog object containing the response
        """
        human_prompt = self.get_human_prompt(prompt, history)

        if callable(load_msg_callback):
            load_msg_callback("Ingesting Command")
            
        try:
            headspace = await self.get_headspace_from_prompt(human_prompt)
            self.logs.debug(f"Using {headspace.name} Headspace")

            if callable(load_msg_callback):
                load_msg_callback("Thinking...")

            dialog = await headspace.query(prompt, stream=True)

            if callable(load_msg_callback):
                load_msg_callback("Formulating Response...")

            return dialog

        except Exception as e:
            self.logs.error(f"Query failed: {e}")
            if callable(load_msg_callback):
                load_msg_callback("Error processing query")
            return None
