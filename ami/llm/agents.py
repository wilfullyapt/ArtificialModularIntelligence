from ami.core import LogBase

#Here are the specifics of your role as a tool calling agent:
#{role}

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
\{
    "action": "tool_name",
    "args": \{
        "arg_name": "arg_value",
        "arg_name": "arg_value",
    \}
\}
```
Observation: action result
<repeat Thought/Action/Observation N times>
Thought: It appears the task is complete
Action:
```
\{
  "action": "TASK COMPLETE",
\}

## Tool Usage Instructions

Use a json blob to specify a tool by providing the action ($TOOL_NAME) and the  ($INPUT).
The only valid "action" values: {tool_names}
Only use the "TASK COMPLETE" value for the action when you think the Human request has been fullfilled.
You can only run one action at a time and observe what happens before taken a subsequent step. DO NOT TAKE TWO ACTIONS AT ONCE.


Begin!
"""

class FunctionCallingThoughActionObservation(LogBase):
    def __init__(self, provider):
        super().__init__()
        self.provider = provider
        self._tools = []

    @property
    def tools(self):
        return self._tools

    @property
    def tool_names(self):
        return ', '.join([ tool.name for tool in self._tools ])

    @property
    def tool_strings(self):
        return '\n'.join([ tool.tool_string for tool in self._tools ])


    def run(self, convo, tools):
        self._tools = tools
        system_prompt = FUNCTION_CALLING_TAO_AGENT_SYSTEM_PROMPT.format(tools=self.tool_strings, tool_names=self.tool_names)

        return system_prompt



# Think and Plan Agent
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
