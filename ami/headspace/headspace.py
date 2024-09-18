""" AMI Headspace Core Funcionality """

from functools import wraps
from pathlib import Path
from types import ModuleType
from typing import Any, List

from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.tools import StructuredTool
from langchain.prompts import ChatPromptTemplate, PromptTemplate
import qrcode

from ami.config import Config
from ami.headspace.base import Primitive

from .dialog import Dialog

def agent_observation(observation:str):
    """ This function converts a result to an observation for the agent """
    return f"Observation: {observation}"

def ami_tool(func):
    """ Decorator for creating tools within AI-controlled classes.

    This decorator marks a function as a tool that can be used by the AI agent.
    It adds an 'is_tool' attribute to the function for easy identification.

    Returns:
        Callable: The decorated function with an added 'is_tool' attribute.
    """
    @wraps(func)
    def wrapper():
        setattr(func, 'is_tool', True)
        return func

    return wrapper()


def generate_qr_image(url) -> Path:
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    qr_img_path = Config().ai_dir / "resources" / "img_dump" / "qr_code.png"
    qr_img_path.parent.mkdir(parents=True, exist_ok=True)

    img.save(qr_img_path)
    return qr_img_path

STRUCTURED_AGENT_USER = """{input}

{agent_scratchpad}
"""

SUMMERIZE_AGENT = """ You are a companion AI.
Your assignment is to summerize your internal monolog and respond back to the human as an AI companion would.
Your inner monolog is things that you have already done. You AI Companion response should be in the past tense.
Your response should be a single sentence, goal orientated without pleasantries.
{additional_visual}

### Inner Monolog / Completed Tasks
{intermediate_steps}

### AI companion Response:
"""

class Headspace(Primitive):
    """ 
    Headspace is an abstract base class that is the framework for an AI-powered AMI agent built
    with natural language capabilities. It is designed to be inherited by subclasses that define
    specific tools and behaviors for the agent.

    The Headspace class handles the creation of a structured chat agent using the LangChain
    library, and provides methods for querying the agent, streaming its responses, and managing
    the dialog history. It also includes functionality for parsing prompts from a separate module
    and handling visual inputs.

    Subclasses of Headspace should define the tools of the agent with the decorator `@ami_tool`,
    the higher level AI that AMI is will implement the tools in an agent and handle the routing
    via the `ROUTING` member of `<headpsace>.prompt.py` module member script found in the
    headspace directory. 

    Key Features:
    - Creation of a structured chat agent with custom tools and prompts
    - Query and streaming methods for interacting with the agent
    - Dialog history management
    - Visual input handling
    - Error handling for parsing errors during agent execution

    Note: The Headspace class cannot be instantiated directly and is intended to be inherited by
    concrete subclasses that define the specific agent functionality.

    Member optionally set by subclass:
        HANDLE_PARSING_ERRORS: Boolean flag how the agent should be handling parsing errors
    """

    HANDLE_PARSING_ERRORS: bool = False

    def __new__(cls, *args, **kwargs):
        """ This class is only inheritable, cannot be instantiated alone """
        if cls is Headspace:
            raise TypeError("Headspace class cannot be instantiated directly.")
        return super().__new__(cls, *args, **kwargs)


    def __init__(self, spawner, prompts):
        """
        Initialize the Headspace instance.

        Args:
            spawner (callable): A function that spawns a language model instance.

        Attributes:
            spawn_llm (callable): The function used to spawn a language model instance.
            dialog (Dialog): An instance of the Dialog class for managing the conversation history.
            agent_response (dict): The response from the agent, including intermediate steps.
            prompts (ModuleType): The module containing the prompts for the agent.
            agent (AgentType): The structured chat agent instance.
            agent_executor (AgentExecutor): The executor for the agent.
        """
        Primitive.__init__(self)

        self.spawn_llm = spawner
        self.prompts: ModuleType = prompts

        self.dialog = Dialog(headspace=self.__class__.__name__)
        self.agent_response = None

        agent_prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", self.prompts.AGENT),
                ("user", STRUCTURED_AGENT_USER)
            ]
        )
        tools = self.get_tools()
        self.agent: Any = create_structured_chat_agent(self.spawn_llm(), tools, agent_prompt_template)
        self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=tools,
                verbose=self.logs.verbose,
                return_intermediate_steps=True,
                handle_parsing_errors=self.HANDLE_PARSING_ERRORS
            )


    def __repr__(self):
        """ Custom __repr__ function for the Headspace instanced """
        return f"Headspace(name={self.name}, spawner={self.spawn_llm.__repr__()})"

    @property
    def name(self):
        return self.__class__.__name__.lower()

    def get_summerize_agent_prompt(self) -> PromptTemplate:
        """
        Generates a prompt template for summarizing the agent's internal monologue.

        Returns:
            PromptTemplate: A prompt template for summarizing the agent's internal monologue.
        """
        summary_prompt = PromptTemplate.from_template(SUMMERIZE_AGENT)
        if self.dialog.visual:
            visual = "Please note you have a visual you are responding with to the human. Whatever step you think you did in the past tense, the human needs to do in the present tense."
        else:
            visual = ""
        return summary_prompt.format(
            additional_visual=visual,
            intermediate_steps=self.agent_response["intermediate_steps"]
        )

    def get_tools(self) -> List[StructuredTool]:
        """ This method can be implemented by the subclass for specific behaivor, but it is not recommended """
        possible_tools = [ member_method
                          for member_method in dir(self)
                          if member_method not in dir(self.__class__.__bases__[0]) ]
        class_methods = [ getattr(self, class_tool) for class_tool in possible_tools ]
        hai_tools = [ member_method
                      for member_method in class_methods
                      if hasattr(member_method, "is_tool") ]
        tools = [ StructuredTool.from_function(func) for func in hai_tools ]
        return tools

    def stream(self):
        """
        Generate a summarized AI companion response based on the agent's internal monologue.

        Returns:
            generator: A summarized AI companion response.
        """
        prompt = self.get_summerize_agent_prompt()
        return self.spawn_llm().stream(prompt, stop=[".", "\n"])

    def think(self):
        """
        Generate a summarized AI companion response based on the agent's internal monologue.

        Returns:
            str: A summarized AI companion response.
        """
        prompt = self.get_summerize_agent_prompt()
        return self.spawn_llm().invoke(prompt, stop=[".", "\n"])

    def query(self, prompt: str, stream=False) -> Dialog:
        """
        Process a user query through the agent and generate a response.

        Args:
            prompt (str): The user's input query.
            stream (bool, optional): Whether to stream the response. Defaults to False.

        Returns:
            Dialog: The updated dialog object containing the query and response.
        """
        self.logs.info(f"Headspace.query(prompt='{prompt}')")
        self.dialog.visual = None

        self.agent_response = self.agent_executor.invoke({"input": prompt})

        if self.agent_response['output'] == "Agent stopped due to iteration limit or time limit.":
            self.logs.warn("Agent stopped due to impossed limitation. Check logs and/or LangSmith")

        self.dialog.timeout = 15 if self.dialog.visual else 3

        if stream:
            ai_response = ("AI", self.stream())
        else:
            ai_response = ("AI", self.think)

        self.dialog.push([ ("Human", prompt), ai_response ])

        return self.dialog
