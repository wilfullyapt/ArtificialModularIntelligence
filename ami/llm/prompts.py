from ami.core import LogBase

class ZeroShot(LogBase):
    def __init__(self, provider):
        super().__init__()
        self.provider = provider

    def invoke(self, prompt: str) -> str:
        try:
            self.logs.debug(prompt)
            self.logs.debug(f"LLM model in use: {self.provider.model}")
            kwargs = {"reasoning_effort": "low", "max_tokens": 500} if self.provider.model in [ "grok-3-mini", "grok-3-mini-fast" ] else {}
            response = self.provider.generate_response(prompt, **kwargs)
            self.logs.debug(response)
            return response
        except Exception as e:
            self.logs.error(f"Error in ZeroShot.invoke: {e}")
            raise
