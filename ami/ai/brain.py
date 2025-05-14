""" The Brain is the meat and potatoes of the AI. Access to LLMs should be managed here """

from typing import List
from functools import cached_property

from ami.core import LogBase, Config, PluginRegistry, Conversation, PluginVertical
from ami.headspace import Headspace
from ami.llm import LLMProvider

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
            registry: Registry managing all plugins including headspaces
        """
        super().__init__()
#       config = Config()
        self.registry = PluginRegistry(process_manager)
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

            self._headspace_cache[key] = self.instance_headspace(plugin.get_vertical(PluginVertical.HEADSPACE))

        return self._headspace_cache[key]

    @cached_property
    def available_headspaces(self) -> List[str]:
        """Get list of available headspace names."""
        return [ plugin.name for plugin in self.registry.get_plugins_by_vertical(PluginVertical.HEADSPACE)]

    def get_human_prompt(self, prompt: str, history: str="") -> str:
        """Generate a prompt string with optional conversation history."""
        if history:
            human_prompt = PromptTemplate.from_template(HUMAN_WITH_MEMORY)
            return human_prompt.format(prompt=prompt, memory=history)

        human_prompt = PromptTemplate.from_template(HUMAN_WITHOUT_MEMORY)
        return human_prompt.format(prompt=prompt)

    @cached_property
    def llm(self):
        return LLMProvider.from_environment()

    def headspace_router(self, query: str):
        """ Given a query, run the zeroshot propmt and return a cached instance of the corrosponding Headspace """

        zero_shot = LLMProvider.from_environment().as_zero_shot()
        result = zero_shot.invoke(
            HEADSPACE_ROUTER,
            {
                "examples": "/n".join(self.registry.routing_examples),
                "headspaces": str(self.registry.names),
                "query": query
            }
        )

        headspace_name = result.strip().split()[0]
        return self[headspace_name]

    def query(self, convo: Conversation) -> str:
        """
        Process a conversation via routing to the Headspace of interest

        Args:
            convo: Conversation > The conversation context for the query

        Returns:
            str: The AI's response
            (note) The return type is a string but this method modifies the Conversation object
        """

        if convo.is_empty():
            self.logs.error("Brain.queue(Conversation) called with an empty Conversation")
            raise ValueError("Brain.queue(Conversation) called with an empty Conversation")

        # TODO: At some point in the future, you will have to pass a better context than "the last thing the human said"
        # The context of the conversation changes the intention
        headspace = self.headspace_router(convo[-1])
        self.logs.debug(f"Headspace router picked '{headspace}'")

        headspace.query(conversation)

# BREAKPOINT BETWEEN NEW AND OLD ###############################

        last_message = conversation.get_last_message(role="human")
        if not last_message:
            self.logs.error("No human message found in conversation")
            return "I couldn't find your message in the conversation."

        context = conversation.get_context(max_messages=5)  # Last 5 messages for context
        history = "\n".join(f"{msg['role'].title()}: {msg['text']}" for msg in context[:-1])  # All but last message
        prompt = last_message["text"]

        # Create prompt with context
        human_prompt = self.get_human_prompt(prompt, history)

        if callable(load_msg_callback):
            load_msg_callback("Ingesting Command")
            
        try:
            headspace = self.get_headspace_from_prompt(human_prompt)
            self.logs.debug(f"Using {headspace.name} Headspace")

            if callable(load_msg_callback):
                load_msg_callback("Thinking...")

            # Pass conversation to headspace
            dialog = headspace.query(conversation, stream=True)

            if callable(load_msg_callback):
                load_msg_callback("Formulating Response...")

            # Extract response text from dialog
            return dialog.get_last_message()["text"] if dialog else "I encountered an error processing your request."

        except Exception as e:
            self.logs.error(f"Query failed: {e}")
            if callable(load_msg_callback):
                load_msg_callback("Error processing query")
            return "I encountered an error processing your request."
