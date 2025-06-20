from typing import Union, List, Dict
from ami.core import LogBase

class ZeroShot(LogBase):
    def __init__(self, provider):
        super().__init__()
        self.provider = provider

    def invoke(self, prompt: Union[str, List[Dict[str, str]]]) -> str:
        try:
#           self.logs.debug(str(prompt))
            self.logs.debug(f"LLM model in use: {self.provider.model}")

            kwargs = {}
            if self.provider.model in [ "grok-3-mini", "grok-3-mini-fast" ]:
                kwargs = {"reasoning_effort": "low", "max_tokens": 500}
                self.logs.info(f"Thinking model '{self.provider.model}' detected, using low effort reasoning.")

            response = self.provider.generate_response(prompt, **kwargs)
#           self.logs.debug(response)
            return response
        except Exception as e:
            self.logs.error(f"Error in ZeroShot.invoke: {e}")
            raise
