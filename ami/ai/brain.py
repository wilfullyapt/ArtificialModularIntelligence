""" The Brain is the meat and potatoes of the AI. Access to LLMs should be managed here """

from typing import Dict, List, Any, Tuple
from functools import cached_property

from ..core import LogBase, Config, PluginRegistry, PluginVertical
from ..headspace import Headspace, HeadspaceInstruction
from ..llm import LLMProvider

HEADSPACE_ROUTER = """You are an AI router designed to responde with the approprate Headspace
to use to fulfill a user request. The HUMAN query will be passed to the approprate Headspace,
so choose carefully. It is very important you only respond with one word.

Here are some examples:

{examples}

Here is a list of your availalbe headspaces:
{headspaces}

Begin!
"""

DEFAULT_PERSONALITY = """
Formal, deferential, and professional, like a dedicated butler who prioritizes the human's needs and speaks with utmost respect and efficiency.
"""

SUMMERIZE_PROMPT = """
You are a companion AI acting as a loyal, professional butler.
Your assignment is to summarize your internal monologue and respond to the human in a formal, service-oriented manner, focusing solely on the completed task.
Your inner monologue consists of actions you have already performed, and your response must reflect these in the past tense.
Your response must be a single sentence, concise, goal-oriented, and free of personal pronouns referring to yourself (e.g., avoid "I" or "my").
The response should include only relevant details, omitting unnecessary steps or pleasantries.

### Personality
{personality}

### Inner Monologue / Completed Tasks
{steps}

### How do you respond?

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

    def __init__(self, ipc_manager: "IPCManager"):
        """ 
        Initialize the Brain instance.

        Args:
            temp_comms: Temporal communications system
            registry: Registry managing all plugins including headspaces
        """
        super().__init__()
#       config = Config()
        self.registry = PluginRegistry(ipc_manager)
        self._headspace_cache = {}
        
    def __contains__(self, value: str):
        """Check if a headspace exists."""
        return value.upper() in self.available_headspaces

    def instance_headspace(self, headspace):
        if not issubclass(headspace, Headspace):
            raise ValueError(f"Headspace({headspace}) is not a subclass for headspacing")
        return headspace()

    def __getitem__(self, headspace_name: str) -> 'HeadspacePlugin':
        """Get a headspace plugin by name."""
        key = headspace_name.lower()
        if key not in self._headspace_cache:
            plugin = self.registry[key]
            if not plugin:
                self.logs.error(f"Headspace({headspace_name}) cannot be found in Brain's Plugin Registry.")
                raise AgentNotFound(f"Headspace({headspace_name}) cannot be found in Brain's Plugin Registry. Check Brain.available_headspaces")

            self.logs.debug(f"Caching {key} Headspace")
            self._headspace_cache[key] = self.instance_headspace(plugin.get_vertical(PluginVertical.HEADSPACE))

        return self._headspace_cache[key]

    @cached_property
    def available_headspaces(self) -> List[str]:
        """Get list of available headspace names."""
        return [ plugin.name for plugin in self.registry.get_plugins_by_vertical(PluginVertical.HEADSPACE)]

    @cached_property
    def personality(self) -> str:
        personality = DEFAULT_PERSONALITY
        personality_prompt_file = Config().data_dir / "personality.prompt"
        if personality_prompt_file.is_file():
            with open(personality_prompt_file, 'r') as ppf:
                personality = ppf.read()
        return personality

    def headspace_router(self, query: str):
        """ Given a query, run the zeroshot propmt and return a cached instance of the corrosponding Headspace """

        zero_shot = LLMProvider.from_environment().as_zero_shot()
        result = zero_shot.invoke(
            [
                { 
                    "role": "system",
                    "content": HEADSPACE_ROUTER.format(
                        **{
                            "examples": "\n".join(self.registry.routing_examples),
                            "headspaces": str(self.registry.names)
                        }
                    )
                },
                {
                    "role": "user",
                    "content": query
                }
            ]
        )

        self.logs.debug(f"Raw headspace router output: {result}")
        headspace_name = result.strip().split()[0]
        return self[headspace_name]

    def summarize(self, steps: List[Dict[str, Any]])  -> str:
        """ Summarize the steps the agent took """
        zero_shot = LLMProvider.from_environment().as_zero_shot()
        result = zero_shot.invoke(
            [
                {
                    "role": "system",
                    "content": SUMMERIZE_PROMPT.format(
                        **{
                            "personality": self.personality,
                            "steps": steps
                        }
                    )
                }
            ]
        )
        return result.strip()

    def query(self, convo: str) -> Tuple[HeadspaceInstruction, str]:
        """
        Process a conversation via routing to the Headspace of interest

        Args:
            convo: Conversation > The conversation context for the query

        Returns:
            str: The AI's response
            (note) The return type is a string but this method modifies the Conversation object
        """

        if not convo:
            err_msg = "Brain.queue(convo: List[Dict[str, str]]) called with an empty convo"
            self.logs.error(err_msg)
            raise ValueError(err_msg)

        headspace = self.headspace_router(str(convo))
        self.logs.debug(f"Headspace router picked '{headspace}'")

        headspace_result = headspace.query(convo)
        return headspace_result, self.summarize(headspace_result.steps)
