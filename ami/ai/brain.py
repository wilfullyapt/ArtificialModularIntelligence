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

from ami.base import Base
from ami.config import Config
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

def get_prompts_as_module(from_module: str) -> ModuleType:
    """ Get a prompt.py file as a module, given a module name """
    module = sys.modules[from_module]
    package_name = module.__package__ or ''
    try:
        package: Any = import_module(package_name)
        path = Path(package.__file__).parent / 'prompts.py'
        if not path.is_file():
            raise FileNotFoundError(f"prompts.py not found in {package.__name__}")
    except ImportError as exc:
        raise ImportError(f"Cannot import package {package_name}") from exc

    spec: Any = spec_from_file_location(path.stem, str(path))
    module = module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module

class AgentNotFound(Exception):
    """ Agent not found exception """
    pass

class HeadspaceCache(BaseModel):
    """
    HeadspaceCache is a Pydantic BaseModel that represents a cache for a Headspace module.
    It stores the name, module, prompts, mode('core' or 'import'), and an instance of the Headspace.
    """
    name: str
    module: Any
    prompts: Any
    mode: Literal['core', 'import']
    _instance: Optional[Any] = None

    class Config:
        arbitrary_types_allowed = True

    def get_instance(self, spawner):
        """ Return instance. Create if absent. """
        if self._instance is None:
            self._instance = self.module(spawner=spawner, prompts=self.prompts)
        return self._instance

    @classmethod
    def from_definition(cls, module: ModuleType):
        """ Instance the pydantic module from a module """
        name = module.__module__.split('.')[-2]
        assert name.lower() == module.__name__.lower()

        if '_core_' in module.__module__:
            mode = 'core'
        elif '_import_' in module.__module__:
            mode = 'import'
        else:
            raise ValueError(f"Invalid module import for {module.__module__}")

        return cls(
            name=name,
            module=module,
            mode=mode,
            prompts=get_prompts_as_module(module.__module__)
        )

class Brain(Base):
    """
    The Brain class is the language processing part of the AI system, responsible for managing
    and coordinating the various Headspaces that resolve the queries with the available Headspaces.
    It acts as a router, determining the appropriate Headspace to handle a given user query, and
    facilitates the interaction between the user and the selected Headspace.
    """

    def __init__(self, headspaces: List=[]):
        """ 
        Initialize the Brain instance.

        Args:
            headspaces (List, optional): A list of Headspace modules to include in the Brain.
                                         Defaults to an empty list.

        Raises:
            FileNotFoundError: If the directory specified in the configuration for storing modules
                               does not exist.
        """
        super().__init__()

        self._headspace_cache = { hs.name.upper() : hs
                            for hs in [ HeadspaceCache.from_definition(hs) for hs in headspaces ]
                      }

        config = Config()
        self.tk =  config["together_apikey"]
#       self.ak =  config["anthropic_apikey"]

        if not config.modules_dir.is_dir():
            raise FileNotFoundError(f"Directory not found: {config.modules_dir}")

    def __contains__(self, value: str):
        """ Check if the value exsits in the cache as a headsapce """
        return value.upper() in self.classes

    def __getitem__(self, cache_name: str):
        """ 
        Retrieve the Headspace instance corresponding to the given cache_name.

        Args:
            cache_name (str): The name of the Headspace to retrieve.

        Returns:
            Any: The Headspace instance.

        Raises:
            AgentNotFound: If the requested Headspace is not found in the Brain.
        """
        cache_name = cache_name.upper()
        if cache_name not in self._headspace_cache:
            self.logs.error(f"Agent({cache_name}) cannot be found in Brain")
            raise AgentNotFound(f"Agent({cache_name}) cannot be found in Brain")
        return self._headspace_cache[cache_name].get_instance(spawner=self.llm_spawner)

    @cached_property
    def routing(self):
        """ Return a list of example router interaction frim the modules. Cached. """
        routes = []
        for hs, cache in self._headspace_cache.items():
            try:
                hs_opt = [ f"HUMAN: {route}\nAI: {hs.upper()}" for route in cache.prompts.ROUTING ]
            except AttributeError as e:
                self.logs.error(f"Cannot load the routing for {hs}! Mising ROUTING in script: {e}")
                hs_opt = []
            routes.extend(hs_opt)
        return routes

    def clear_routing_cache(self):
        """ Clear the roughting for Brain.routing """
        if 'routing' in self.__dict__:
            del self.__dict__['routing']

    @property
    def classes(self):
        """ Return the available Headspace cached """
        return [ key.upper() for key in self._headspace_cache.keys() ]

    def llm_spawner(self,
                    model_name="mistralai/Mistral-7B-Instruct-v0.2",
                    temperature=0,
                    top_k=1,
                    max_tokens=200):
        """ Return an instance Language Model from LangChain """
        model_name = "meta-llama/Llama-3-8b-chat-hf"
        return Together(model=model_name,
                        temperature=temperature,
                        top_k=top_k,
                        together_api_key=self.tk,
                        max_tokens=max_tokens)

    def mixtral_llm(self, max_tokens=256):
        """ Return an instance Language Model from LangChain """
        model = "mistralai/Mistral-7B-Instruct-v0.2"
        return Together(model=model,
                        temperature=0,
                        top_k=1,
                        max_tokens=max_tokens,
                        together_api_key=self.tk)

    def get_human_prompt(self, prompt: str, history: str="") -> str:
        """ 
        Generates a prompt string for the LLM, including optional conversation history.

        Args:
            prompt (str): The user's input query.
            history (str, optional): The conversation history to provide context. Defaults to "".

        Returns:
        str: The formatted prompt string, including conversation history if provided.
        """
        if history != "":
            human_prompt = PromptTemplate.from_template(HUMAN_WITH_MEMORY)
            return human_prompt.format(prompt=prompt, memory=history)

        human_prompt = PromptTemplate.from_template(HUMAN_WITHOUT_MEMORY)
        return human_prompt.format(prompt=prompt)

    def get_headspace_from_prompt(self, query: str):
        """ 
        Determine the appropriate Headspace to use for a given user query.

        Args:
            query (str): The user's input query.

        Returns:
            Headspace: The appropriate Headspace instance to handle the query.
        """
        prompt = ChatPromptTemplate.from_template(HEADSPACE_ROUTER)
        chain = prompt | self.mixtral_llm() | StrOutputParser()

        examples = "\n\n".join(self.routing)
        options = str(self.classes)
        result = chain.invoke({"examples": examples,"headspaces": options, "query": query})
        headspace_name = result.strip().split()[0]

        return self[headspace_name]

    def query(self, prompt: str, history: str="", load_msg_callback=None) -> Dialog:
        """
        Query the AI with a given prompt and optional conversation history.

        Args:
            prompt (str): The user's input query.
            history (str, optional): The conversation history to provide context. Defaults to "".
            load_msg_callback (Callable, optional): A callback function to display loading messages.
                                                    Defaults to None.

        Returns:
            Dialog: The AI's response as a Dialog object.
        """
        human_prompt = self.get_human_prompt(prompt, history)

        if isinstance(load_msg_callback, Callable):
            load_msg_callback("Ingesting Commmand")
        headspace = self.get_headspace_from_prompt(human_prompt)
        self.logs.debug(f"The AI has choosen to use the {headspace.name} Headspace.")

        if isinstance(load_msg_callback, Callable):
            load_msg_callback("Thinking ...")
        dialog = headspace.query(prompt, stream=True)
        if isinstance(load_msg_callback, Callable):
            load_msg_callback("Formulating Response ...")

        return dialog
