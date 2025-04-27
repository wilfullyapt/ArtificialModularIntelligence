"""LLM Client for making requests to language models."""
from typing import Dict, List, Optional, Union

from ami.core.config import Config

class LLMClient:
    """Base class for LLM clients."""
    
    def __init__(self, model: str, api_key: Optional[str] = None):
        """Initialize the LLM client.
        
        Args:
            model: The model identifier to use
            api_key: Optional API key for authentication
        """

        env_filepath = Config().enviornment_variables_filepath
        #TODO Load the env_filepath to the enviornment
        # Then we can grab the API key.
        # This functionality should happen with the llm client setup

        self.model = model
        self.api_key = api_key
        
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[Union[str, List[str]]] = None,
        **kwargs
    ) -> str:
        """Generate text from the language model.
        
        Args:
            prompt: The input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stop: Stop sequences
            **kwargs: Additional model-specific parameters
            
        Returns:
            Generated text response
        """
        raise NotImplementedError
        
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[Union[str, List[str]]] = None,
        **kwargs
    ) -> str:
        """Have a chat conversation with the language model.
        
        Args:
            messages: List of message dictionaries with role and content
            temperature: Sampling temperature  
            max_tokens: Maximum tokens to generate
            stop: Stop sequences
            **kwargs: Additional model-specific parameters
            
        Returns:
            Model's response message
        """
        raise NotImplementedError
