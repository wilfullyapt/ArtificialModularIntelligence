from ami.core import LogBase

class ZeroShot(LogBase):
    def __init__(self, provider):
        super().__init__()
        self.provider = provider

    def invoke(self, template: str, inputs: dict) -> str:
        try:
            prompt = template.format(**inputs)
            self.logs.debug(prompt)
            response = self.provider.generate_response(prompt)
            self.logs.debug(response)
            return response
        except Exception as e:
            self.logs.error(f"Error in ZeroShot.invoke: {e}")
            raise
