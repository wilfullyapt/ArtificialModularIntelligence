from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Union

from ..core import LogBase

class InstructionType(Enum):
    RELOAD_GUI = "RELOAD_GUI"
    STOP_AGENT = "STOP_AGENT"
    ASK_USER_INPUT = "ASK_USER_INPUT"
    PROVIDE_IMAGE_PATH = "PROVIDE_IMAGE_PATH"
    CONFIRM_WITH_HUMAN = "CONFIRM_WITH_HUMAN"
    INLINE_POPUP = "INLINE_POPUP"

class HeadspaceInstruction(LogBase):
    """A standardized instruction returned by tools or the agent."""
    
    def __init__(
            self,
            instructions: List[InstructionType],
            observation: str,
            name: Optional[str] = None,
            should_continue: Optional[bool] = None,
            steps: Optional[List[Dict]] = None,
            **kwargs
    ):
        """ The HeadspaceInstruction are kind of a catch all for agents to instuct the AI or Brain """
        self.instructions = instructions
        self.observation = observation
        self.name = name
        self.should_continue = should_continue
        self.steps = steps or []
        self.data = kwargs                                  # any kwargs are captured in the data transmiseded
        self.logs.debug(f"HeadspaceInstruction: {self}")

    @property
    def as_dict(self):
        """Return a serializable dictionary representation."""
        return {
            "types": [instr.name for instr in self.instructions],
            "observation": self.observation,
            "should_continue": self.should_continue,
            "data": self.data
        }

    @property
    def as_steps(self):
        """Return a serialized dictionary representing the steps."""
        return {
            "types": [instr.name for instr in self.instructions],
            "steps": self.steps,
            "data": self.data
        }

    @classmethod
    def from_steps(cls, steps: List[Dict], name: str) -> 'HeadspaceInstruction':
        """Create a HeadspaceInstruction from a list of steps, aggregating all instruction types except STOP_AGENT."""
        if not steps:
            return cls(
                instructions=[],
                observation="No steps executed",
                name=name,
                should_continue=False,
                steps=steps
            )
        
        instructions_set = set()
        for step in steps:
            # Check for 'instructions' key directly in the step
            if 'instructions' in step and isinstance(step['instructions'], list):
                for instr_str in step['instructions']:
                    if instr_str != "STOP_AGENT":
                        try:
                            instr_type = InstructionType[instr_str]
                            instructions_set.add(instr_type)
                        except KeyError:
                            # Invalid instruction type; silently skip for now
                            pass
            # Also check observation for 'types' to support alternative formats
            obs = step.get("observation")
            if isinstance(obs, dict) and "types" in obs:
                for instr_str in obs["types"]:
                    if instr_str != "STOP_AGENT":
                        try:
                            instr_type = InstructionType[instr_str]
                            instructions_set.add(instr_type)
                        except KeyError:
                            pass
        
        # Determine final observation and continuation based on the last step
        last_step = steps[-1]
        if last_step["action"]["action"] == "TASK COMPLETE":
            observation = "Task completed"
            should_continue = False
        elif isinstance(last_step.get("observation"), dict) and "observation" in last_step["observation"] and "should_continue" in last_step["observation"]:
            observation = last_step["observation"]["observation"]
            should_continue = last_step["observation"]["should_continue"]
        else:
            observation = "Max steps reached"
            should_continue = False
        
        return cls(
            instructions=list(instructions_set),
            observation=observation,
            name=name,
            should_continue=should_continue,
            steps=steps
        )

    @classmethod
    def reload_gui(cls, observation: str) -> 'HeadspaceInstruction':
        """Instruct to reload the GUI."""
        return cls(instructions=[InstructionType.RELOAD_GUI], observation=observation, should_continue=True)

    @classmethod
    def popup_markdown(cls, observation: str) -> 'HeadspaceInstruction':
        """Instruct to reload the GUI."""
        return cls(instructions=[InstructionType.INLINE_POPUP], observation=observation, should_continue=True)

    @classmethod
    def popup_injection(cls, observation: str) -> 'HeadspaceInstruction':
        """Instruct to reload the GUI."""
        return cls(instructions=[InstructionType.INLINE_POPUP], observation=observation, should_continue=True)

    @classmethod
    def stop_agent(cls, observation: str) -> 'HeadspaceInstruction':
        """Instruct to stop the agent."""
        return cls(instructions=[InstructionType.STOP_AGENT], observation=observation, should_continue=False)

    @classmethod
    def ask_user_input(cls, observation: str, question: str) -> 'HeadspaceInstruction':
        """Instruct to get user input."""
        return cls(instructions=[InstructionType.ASK_USER_INPUT], observation=observation, should_continue=True, question=question)

    @classmethod
    def provide_image_path(cls, observation: str, image_path:  Path) -> 'HeadspaceInstruction':
        """Instruct to handle an image path."""
        return cls(instructions=[InstructionType.PROVIDE_IMAGE_PATH], observation=observation, should_continue=True, image_path=image_path)


