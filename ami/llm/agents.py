import re
import json
import traceback
from datetime import datetime
from functools import cached_property
from typing import Dict, List, Any, Tuple

from ami.core import LogBase, Config

FUNCTION_CALLING_TAO_AGENT_SYSTEM_PROMPT = """
You are an AI tool calling agent. You run in a cognitive loop to accomplish tasks at the user's behest.
You are designed to think about how to fullfil the human request, make python function calls, observe the result of the function, and decide when the request is fullfilled.
You should first think about the tasks at hand and the sequence of tools to complete the objective.

## You have access to the following tool:
{tools}

## Output Format

To fullfil the Human's request, please use the following format:

Human: Input request
Thought: Use active listening to reiterate the Human's query in a way you can better understand the intentions of the Human and think about the steps to take to complete the Human's goal
Action:
```$JSON_BLOB
{{
    "action": "tool_name",
    "args": {{
        "arg_name": "arg_value",
        "arg_name": "arg_value",
    }}
}}
```
Observation: action result
<repeat Thought/Action/Observation N times>
Thought: It appears the task is complete
Action:
```
{{
  "action": "TASK COMPLETE",
}}

## Tool Usage Instructions

Use a json blob to specify a tool by providing the action ($TOOL_NAME) and the  ($INPUT).
The only valid "action" values: {tool_names}
Only use the "TASK COMPLETE" value for the action when you think the Human request has been fullfilled.
You can only run one action at a time and observe what happens before taken a subsequent step. DO NOT TAKE TWO ACTIONS AT ONCE.


Begin!
"""


def parse_llm_output(output: str) -> tuple[str, dict]:
    """
    Parse LLM output to extract thought and action components.
    
    Args:
        output: String containing the LLM output with Thought and Action sections
        
    Returns:
        tuple: (thought_text, action_dict) where thought_text is the thought string
              and action_dict is the parsed JSON action
              
    Raises:
        ValueError: If the output format is invalid or JSON cannot be parsed
    """
    thought_match = re.search(r'Thought:\s*(.*?)(?=\n\nAction:|$)', output, re.DOTALL)
    if not thought_match:
        raise ValueError("No Thought section found in output")
    
    thought_text = thought_match.group(1).strip()
    
    action_match = re.search(r'Action:\s*```json\n(.*?)\n```', output, re.DOTALL)
    if not action_match:
        raise ValueError("No Action section found in output")
    
    try:
        action_dict = json.loads(action_match.group(1))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in Action section: {str(e)}")
    
    return thought_text, action_dict

class FunctionCallingThoughActionObservation(LogBase):
    """
    This is the function calling agent designed to:
        - Thought: This is a thought about the task in context of an objective:
        - Action: This is a JSON based acted for a tool use
        - Observation: This is an observation on the action/function results
    """

    def __init__(self, client, headspace_name: str):
        super().__init__()
        self.client = client
        self.steps = []
        self.logfile = Config().convos_dir / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}_{headspace_name}.log"

    @cached_property
    def llm_call(self):
        if hasattr(self.client, "custom_tool_call_"):
            self.logs.debug("Tool calling agent using the 'custom_tool_call' function in the associated client")
            return self.client.custom_tool_call
        self.logs.debug("Tool calling agent using the 'generate_response' function in the associated client")
        return self.client.generate_response

    def _log_steps_to_file(self) -> None:
        """Write captured steps to a file in JSON format."""
        self.logs.debug(f"Logging steps to {self.logfile}")
        try:
            with open(self.logfile, 'w') as f:
                json.dump(self.steps, f, indent=4)
            self.logs.info(f"Steps successfully logged to {self.logfile}")
        except Exception as e:
            self.logs.error(f"Failed to write steps to {self.logfile}: {str(e)}")

    def think(self) -> Tuple[str, Dict[str, Any], str]:
        """Generate thought and action based on current messages."""
        self.logs.debug("Generating thought and action.")
        full_response = self.llm_call(self.messages, max_tokens=1000)
        try:
            print(full_response)
            thought, action = parse_llm_output(full_response)
            self.logs.debug(f"Thought: {thought}, Action: {action}")
            return thought, action, full_response
        except ValueError as e:
            self.logs.error(f"Failed to parse LLM output: {str(e)}")
            raise

    def act(self, action: Dict[str, Any], tools: List[Any]) -> str:
        """Execute the specified action using available tools."""
        self.logs.debug(f"Executing action: {action}")
        tool = next((t for t in tools if t.name == action["action"]), None)
        if not tool:
            error_msg = f"Tool {action['action']} not found."
            self.logs.error(error_msg)
            return error_msg
        
        try:
            observation = tool.method(**action["args"])
            self.logs.debug(f"Observation: {observation}")
            return observation
        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            self.logs.error(error_msg)
            return error_msg

    def observe(self, full_response: str, observation: str) -> None:
        """Update conversation history with response and observation."""
        self.logs.debug(f"Observing: {observation}")
        self.messages.append({"role": "assistant", "content": full_response})
        self.messages.append({"role": "user", "content": f"Observation: {observation}"})

    def _step(self, tools: List[Any]) -> None:
        """Execute a single think-act-observe step."""
        thought, action, full_response = self.think()
        step_data = {"thought": thought, "action": action}
        self.steps.append(step_data)

        if action["action"] != "TASK COMPLETE":
            observation = self.act(action, tools)
            step_data["observation"] = observation
            self.observe(full_response, observation)

    def _should_continue(self) -> bool:
        """Determine if the loop should continue based on the latest action."""
        if not self.steps:
            return True
        last_action = self.steps[-1]["action"]
        return last_action["action"] != "TASK COMPLETE"

    def run(self, prompt: str, tools: List[Any], max_steps: int = 6) -> List[Dict[str, Any]]:
        """
        Run the agent loop to process the user prompt.

        Args:
            prompt: Initial user request.
            tools: List of available tools.
            max_steps: Maximum number of steps to prevent infinite loops.

        Returns:
            List of steps taken during execution.
        """
        tool_names = ', '.join([tool.name for tool in tools])
        tool_strings = '\n'.join([tool.tool_string for tool in tools])
        system_prompt = FUNCTION_CALLING_TAO_AGENT_SYSTEM_PROMPT.format(tools=tool_strings, tool_names=tool_names)
        self.messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]
        self.steps = []

        try:
            step_count = 0
            while step_count < max_steps and self._should_continue():
                self._step(tools)
                step_count += 1
            if step_count >= max_steps:
                self.logs.warning("Maximum steps reached without task completion.")
        except Exception as e:
            traceback.print_exc()
            print(e)
            self.logs.error(f"Error in function calling agent: {e}")
        finally:
            self._log_steps_to_file()

        return self.steps

class ThinkAndPlanAgent(LogBase):
    def __init__(self, provider):
        super().__init__()
        self.provider = provider

    def run(self, query: str, tools: list) -> str:
        """Think about the query, plan, and execute."""
        think_prompt = f"Analyze and think about this query: {query}. Provide a step-by-step plan."
        plan = self.provider.generate_text(think_prompt, max_tokens=200, **kwargs)
        self.logs.info(f"Generated plan: {plan}")
        
        execute_prompt = f"Based on this plan, provide a response:\n{plan}"
        result = self.provider.generate_text(execute_prompt, max_tokens=300, **kwargs)
        return result

# ReAct Agent
class ReActAgent(LogBase):
    def __init__(self, provider):
        super().__init__()
        self.provider = provider

    def run(self, query: str, max_steps: int = 5, **kwargs) -> str:
        """Reason and act iteratively until resolution."""
        thoughts = []
        current_state = query
        
        for step in range(max_steps):
            reason_prompt = f"Reason about this: {current_state}. What should be done next?"
            thought = self.provider.generate_text(reason_prompt, max_tokens=150, **kwargs)
            thoughts.append(thought)
            self.logs.info(f"Step {step + 1}: {thought}")
            
            action_prompt = f"Based on this reasoning: '{thought}', decide the next action or 'finish' if complete."
            action = self.provider.generate_text(action_prompt, max_tokens=50, **kwargs).strip().lower()
            
            if action == "finish":
                break
            current_state = f"{current_state}\nAction: {action}"
        
        return "\n".join(thoughts)
