""" AMI Headspace Abstract Base Class and Core Funcionality """

import json
import typing
import inspect
from pathlib import Path
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional
from functools import cached_property, wraps

import qrcode

from ..core import Config
from ..llm import LLMProvider

from .base import Primitive
from .headspace_instructions import HeadspaceInstruction

def ami_tool(prereqs: Optional[List[str]] = None):
    """ Decorator for creating tools within AI-controlled classes.

    This decorator marks a function as a tool that can be used by the AI agent.
    It adds an 'is_tool' attribute to the function for easy identification.
    Optionally accepts a list of prerequisite method names (strings) whose results
    will be dynamically appended to the tool's description in the system prompt
    for contextual awareness (e.g., @ami_tool(['list_lists'])).

    Args:
        prereqs: List of strings naming prerequisite methods to call for context.

    Returns:
        Callable: The decorated function with added 'is_tool' and 'prerequisites' attributes.
    """
    if prereqs is None:
        prereqs = []
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        wrapper.is_tool = True
        wrapper.prerequisites = prereqs
        return wrapper
    return decorator

def generate_qr_image(url) -> Path:
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    qr_img_path = Config().data_dir / "resources" / "img_dump" / "qr_code.png"
    qr_img_path.parent.mkdir(parents=True, exist_ok=True)

    img.save(qr_img_path)
    return qr_img_path

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
    def from_method(cls, method: Callable, enhanced_description: Optional[str] = None) -> 'HeadspaceTool':
        func = method.__func__ if hasattr(method, '__func__') else method
        tool_info = extract_tool_info(func)
        description = enhanced_description or tool_info["description"]
        return cls(
                name = tool_info["name"],
                description = description,
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
    """

    def __new__(cls, *args, **kwargs):
        """ This class is only inheritable, cannot be instantiated alone """
        if cls is Headspace:
            raise TypeError("Headspace class cannot be instantiated directly.")
        return super().__new__(cls, *args, **kwargs)

    def __repr__(self):
        """ Custom __repr__ function for the Headspace instanced """
        return f"<Headspace(name={self.name})>"

    @cached_property
    def tool_names(self):
        return ', '.join([ tool.name for tool in self.tools ])

    @cached_property
    def tool_strings(self):
        return '\n'.join([ tool.tool_string for tool in self.tools ])

    @cached_property
    def tools(self) -> List[HeadspaceTool]:
        """ This method can be implemented by the subclass for specific behavior, but it is not recommended """
        # Get instance methods not in the base class
        base_dir = dir(self.__class__.__bases__[0])
        possible_names = [name for name in dir(self) if name not in base_dir and not name.startswith('_')]
        class_methods = [getattr(self, name) for name in possible_names]
        
        # Filter to tool methods (using __func__ for attribute check)
        hai_tools = [mthd for mthd in class_methods if hasattr(getattr(mthd, '__func__', mthd), 'is_tool')]
        
        tools = []
        for mthd in hai_tools:
            func = getattr(mthd, '__func__', mthd)
            tool_info = extract_tool_info(func)
            
            # Check for prerequisites and enhance description with their results
            enhanced_description = tool_info["description"]
            if hasattr(func, 'prerequisites') and func.prerequisites:
                prereqs = func.prerequisites
                context_parts = []
                for prereq_name in prereqs:
                    try:
                        prereq_mthd = getattr(self, prereq_name)
                        if callable(prereq_mthd):
                            result = prereq_mthd()
                            context_str = str(result) if not isinstance(result, str) else result
                            context_parts.append(context_str)
                    except Exception as e:
                        # Log warning if needed; for now, append error as context
                        context_parts.append(f"Error retrieving prerequisite '{prereq_name}': {str(e)}")
                
                if context_parts:
                    enhanced_description += f"\n\nPrerequisite context (use this to inform tool usage): {'; '.join(context_parts)}"
            
            tool = HeadspaceTool.from_method(mthd, enhanced_description=enhanced_description)
            tools.append(tool)
        
        return tools
    
    def append_visual(self, img_path: Path):
        print(f"Image appended to Headspace returning: {img_path}")

    def query(self, prompt: str) -> HeadspaceInstruction:
        """ Process a user query according to the tools in the child headspace object """
        agent = LLMProvider.from_environment().as_funccalling_toa_agent(self.name)

        return agent.run(prompt, self.tools)
