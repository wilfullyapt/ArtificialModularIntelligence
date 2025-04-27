"""Extended Brain module that integrates LLM components with the existing Brain."""

from typing import Any, Dict, List, Optional, Type, Union
from dataclasses import dataclass
from pathlib import Path

from ami.headspace.registry import Registry, ComponentType
from ami.llm.client import LLMClient
from ami.llm.react import ReActAgent
from ami.llm.agent import ThinkAndPlanAgent
from ami.headspace import Dialog
from .brain import Brain, HEADSPACE_ROUTER

@dataclass
class LLMPromptTemplate:
    """Template for LLM system prompts."""
    name: str
    content: str
    required_tools: List[str] = None
    metadata: Dict[str, Any] = None

class BrainLLM(Brain):
    """
    Extended Brain class that integrates LLM capabilities while preserving
    existing Brain functionality.
    """

    def __init__(self, temp_comms, headspaces: List = [], registry: Registry = None):
        """Initialize the BrainLLM.
        
        Args:
            temp_comms: Temporary communications object
            headspaces: List of headspace modules
            registry: Optional Registry instance for managing components
        """
        super().__init__(temp_comms=temp_comms, headspaces=headspaces)
        
        self.registry = registry
        if registry:
            # Initialize LLM components if registry is provided
            self.llm_client = LLMClient(model=self.get_default_model())
            self.react_agent = ReActAgent(tools=self._get_tools(), llm_client=self.llm_client)
            self.think_agent = ThinkAndPlanAgent(llm_client=self.llm_client)
            
            # Load LLM prompt templates
            self._load_llm_prompt_templates()

    def get_default_model(self) -> str:
        """Get default model name based on configuration."""
        return "mistralai/Mistral-7B-Instruct-v0.2"  # Use same as parent class

    def _load_llm_prompt_templates(self):
        """Load LLM prompt templates from registered components."""
        self.llm_prompt_templates = {}
        
        if not self.registry:
            return
            
        # Get all prompt components from registry
        prompt_modules = self.registry.get_all_components(ComponentType.HEADSPACE)
        
        for name, module in prompt_modules.items():
            if hasattr(module, 'llm_prompts'):
                for prompt in module.llm_prompts:
                    if isinstance(prompt, LLMPromptTemplate):
                        self.llm_prompt_templates[prompt.name] = prompt
                        
        self.logs.info(f"Loaded {len(self.llm_prompt_templates)} LLM prompt templates")

    def _get_tools(self) -> Dict[str, Any]:
        """Get available tools from registered components."""
        tools = {}
        
        if not self.registry:
            return tools
            
        # Get all blueprint components that might provide tools
        blueprint_modules = self.registry.get_all_components(ComponentType.BLUEPRINT)
        
        for name, module in blueprint_modules.items():
            if hasattr(module, 'tools'):
                tools.update(module.tools)
                
        return tools

    async def route_llm_prompt(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Union[str, Dialog]:
        """
        Route the incoming message to appropriate LLM prompt template and agent.
        
        Args:
            message: User input message
            context: Optional context information
            
        Returns:
            Response from the appropriate agent or Dialog object
        """
        try:
            # First try standard headspace routing
            try:
                return await self.query(message)
            except Exception as e:
                self.logs.debug(f"Standard routing failed, trying LLM routing: {e}")
            
            # Fallback to LLM routing if headspace routing fails
            template = await self._select_llm_template(message)
            
            if not template:
                # Use default LLM generation
                return await self.llm_client.generate(message)
                
            # Check if tools are required
            if template.required_tools:
                # Use ReAct agent for tool-based tasks
                result = await self.react_agent.run(
                    task=message,
                    context={
                        "prompt_template": template,
                        **(context or {})
                    }
                )
                return result["result"]
                
            # For thinking/planning tasks
            if "think" in template.name.lower() or "plan" in template.name.lower():
                result = await self.think_agent.solve(
                    problem=message,
                    context={
                        "prompt_template": template,
                        **(context or {})
                    }
                )
                return result["solution"]
                
            # Default to direct LLM interaction with template
            prompt = template.content.format(
                message=message,
                **(context or {})
            )
            return await self.llm_client.generate(prompt)
            
        except Exception as e:
            self.logs.error(f"Error in LLM prompt routing: {e}")
            # Fallback to simple message echo in case of errors
            return f"Error processing message: {str(e)}"
            
    async def _select_llm_template(
        self,
        message: str
    ) -> Optional[LLMPromptTemplate]:
        """
        Select the most appropriate LLM prompt template for the message.
        
        Args:
            message: User input message
            
        Returns:
            Selected prompt template or None if no suitable template found
        """
        # TODO: Implement more sophisticated template selection
        # Could use embeddings, classification, or rule-based matching
        
        # Simple keyword matching for now
        for template in self.llm_prompt_templates.values():
            if any(keyword.lower() in message.lower() 
                  for keyword in template.metadata.get('keywords', [])):
                return template
                
        return None
        
    def reload_llm_prompts(self):
        """Reload LLM prompt templates from registry."""
        self._load_llm_prompt_templates()
        
    def add_tool(self, name: str, tool_fn: Any):
        """
        Add a new tool to the ReAct agent.
        
        Args:
            name: Name of the tool
            tool_fn: Tool function
        """
        if hasattr(self, 'react_agent'):
            self.react_agent.tools[name] = tool_fn