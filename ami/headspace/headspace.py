""" AMI Headspace Core Funcionality """

import json
import typing
import inspect
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Callable, Dict, List
from functools import cached_property, wraps

from langchain.tools import StructuredTool
import qrcode

from ami.core import Config, Conversation
from ami.headspace import Primitive
from ami.llm.provider import LLMProvider

from .dialog import Dialog

def agent_observation(observation:str):
    """ This function converts a result to an observation for the agent """
#   return f"Observation: {observation}"
    return f"{observation}\n"

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


def get_param_type(annotation):
    """Convert Python type annotations to a JSON-compatible format."""
    origin = typing.get_origin(annotation)
    if origin is typing.Literal:
        args = typing.get_args(annotation)
        return {"type": "string", "enum": list(args)}
    elif origin is typing.Union and len(typing.get_args(annotation)) == 2 and type(None) in typing.get_args(annotation):
        actual_type = next(a for a in typing.get_args(annotation) if a is not type(None))
        return get_param_type(actual_type)
    elif annotation is int:
        return "integer"
    elif annotation is str:
        return "string"
    elif annotation is bool:
        return "boolean"
    else:
        raise ValueError(f"Unsupported parameter type: {annotation}")

def extract_tool_info(func):
    """Extract name, description, and parameters from a tool function."""
    sig = inspect.signature(func)
    description = func.__doc__.strip().split('\n')[0] if func.__doc__ else ""
    parameters = {}
    for param_name, param in sig.parameters.items():
        if param_name == 'self':
            continue
        if param.annotation is inspect.Parameter.empty:
            raise ValueError(f"Parameter '{param_name}' in '{func.__name__}' has no type annotation")
        param_type = get_param_type(param.annotation)
        param_info = {"type": param_type}
        if param.default is not inspect.Parameter.empty:
            param_info['required'] = False
            param_info["default"] = param.default
        else:
            param_info['required'] = True
        parameters[param_name] = param_info
    return {
        "name": func.__name__,
        "description": description,
        "arg_schema": parameters
    }

#@dataclass
#class ToolArgSchema:


@dataclass
class HeadspaceTool:
    name: str
    description: str
    arg_schema: Dict[str, Dict[str, str|dict]]
    method: Callable

    def __str__(self) -> str:
        data = {
            "name": self.name,
            "description": self.description,
            "arg_schema": self.arg_schema
        }
        return json.dumps(data, indent=2)

    @property
    def tool_string(self) -> str:
        return f"{self.name}({', '.join([ f'{an}: {av}' for an, av in self.arg_schema.items()])}) - {self.description}"

    @classmethod
    def from_method(cls, method: Callable) -> 'HeadspaceTool':
        tool_info = extract_tool_info(method)
        return cls(
                name = tool_info["name"],
                description = tool_info["description"],
                arg_schema = tool_info["arg_schema"],
                method = method
        )

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


    def __init__(self):
        """
        Initialize the Headspace instance.
        """
        Primitive.__init__(self)


#       agent_prompt_template = ChatPromptTemplate.from_messages(
#           [
#               ("system", self.prompts.AGENT),
#               ("user", STRUCTURED_AGENT_USER)
#           ]
#       )
#       tools = self.get_tools()
#       self.agent: Any = create_structured_chat_agent(self.spawn_llm(), tools, agent_prompt_template)
#       self.agent_executor = AgentExecutor(
#               agent=self.agent,
#               tools=tools,
#               verbose=self.logs.verbose,
#               return_intermediate_steps=True,
#               handle_parsing_errors=self.HANDLE_PARSING_ERRORS
#           )

#       model = self.spawn_llm()
#       planner = load_chat_planner(model)
#       executor = load_agent_executor(model, tools, verbose=True)
#       agent = PlanAndExecute(planner=planner, executor=executor)


    def __repr__(self):
        """ Custom __repr__ function for the Headspace instanced """
        return f"Headspace(name={self.name})"

    @cached_property
    def name(self):
        return self.__class__.__name__.lower()

    @property
    def role(self):
        if hasattr(self, "agent_role"):
            return f"Here are the specifics of your agent nature: {self.agent_role}"
        else:
            return ""

    @cached_property
    def tool_names(self):
        return ', '.join([ tool.name for tool in self.tools ])

    @cached_property
    def tool_strings(self):
        return '\n'.join([ tool.tool_string for tool in self.tools ])

    @property
    def AGENT_SYSTEM_PROMPT(self) -> str:
        return FUNCTION_CALLING_AGENT_SYSTEM_PROMPT.format(
            role=self.role,
            tools=str(self.tools),
            tool_names=self.tool_names
        )

    def get_summerize_agent_prompt(self) -> Any:
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

# TODO:
        # TODO:
        # Need to have the convo agent at the headpace leve for the tools to use and modify
        # I feel like each Conversation should have a state
        # ConversationState: WAITING_ANSWER, COMMAND, ZERO_SHOT, FINISHED, ARCHIVED
        # There should be macro function in the Headspace Parent that modifies the convo in a standard way + State
        # Conversation && Brain.query && Headspace && AI.query
        # TODO: ^^^ Make all these objects work together ^^^

#   def human_response(self, ai_response: str):
#       self._convo.ai_response(ai_response)
#       self._convo.state = ConversationType.WAITING_ANSWER
#   def query(self, convo: Conversation, stream: bool=False) -> Conversation:
#       self._convo = convo
#       self.agent.run(convo[-1])

# TODO:

    @property
    def convo(self):
        if self.conversation is None:
            raise ValueError("Conversation member not set!")
        return self.conversation

    @convo.setter
    def convo(self, value: Conversation):
        if not isinstance(value, Conversation):
            raise ValueError("convo member must be of type Conversation!")
        self.conversation = value

    @cached_property
    def tools(self) -> List[HeadspaceTool]:
        """ This method can be implemented by the subclass for specific behaivor, but it is not recommended """
        possible_tools = [ member_method
            for member_method in dir(self)
            if member_method not in dir(self.__class__.__bases__[0]) ]
        class_methods = [ getattr(self, class_tool) for class_tool in possible_tools ]
        hai_tools = [ member_method
            for member_method in class_methods
            if hasattr(member_method, "is_tool") ]
        tools = [ HeadspaceTool.from_method(mthd) for mthd in hai_tools ]
        return tools

    def query(self, conversation: Conversation) -> Conversation:
        """ Process a user query according to the tools in the child headspace opbject """
        agent = LLMProvider.from_environment().as_funccalling_toa_agent()
        return agent.run(conversation.transcript, self.tools)

    def query_old(self, conversation: Conversation, stream: bool=False) -> Dialog:
        """
        Process a user query through the agent and generate a response.

        Args:
            conversation (Conversation): The current conversation object
            stream (bool, optional): Whether to stream the response. Defaults to False.

        Returns:
            Dialog: The updated dialog object containing the query and response.
        """
        # Get the last human message
        last_message = conversation.get_last_message(role="human")
        if not last_message:
            self.logs.error("No human message found in conversation")
            return None

        prompt = last_message["text"]
        self.logs.info(f"Headspace.query(prompt='{prompt}')")
        self.dialog.visual = None

        # Execute agent with prompt
        self.agent_response = self.agent_executor.invoke({"input": prompt})

        if self.agent_response['output'] == "Agent stopped due to iteration limit or time limit.":
            self.logs.warn("Agent stopped due to impossed limitation. Check logs and/or LangSmith")

        # Handle visual content
        self.dialog.timeout = 15 if self.dialog.visual else 3

        # Generate response
        if stream:
            ai_response = ("AI", self.stream())
        else:
            ai_response = ("AI", self.think())

        # Update dialog
        self.dialog.push([("Human", prompt), ai_response])

        # Update conversation state based on response
        if self.dialog.visual:
            # Add any visual files to conversation
            for key, path in self.dialog.visual.items():
                conversation.add_file(key, path)

        return self.dialog
