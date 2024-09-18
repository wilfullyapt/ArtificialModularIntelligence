from ami import headspace
from ami.config import Config
from ami.headspace import Headspace, ami_tool, agent_observation, generate_qr_image
from ami.flask.manager import get_network_url

from .tool import Utils as UtilsTool

class Utils(Headspace):
    """ Built-in Utility Headspace """

    HANDLE_PARSING_ERRORS: bool = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        config = Config()
        self.headspaces = config.enabled_headspaces
        self.get_headspace_dir = config.get_headspace_dir
        self.tool = UtilsTool()

    @ami_tool
    def see_headspaces(self):
        """ Return a list of avialible headspaces """
        return agent_observation(f"Enabled Headspace: {self.headspaces}")

    @ami_tool
    def edit_config(self, headspace_name: str):
        """ Use this tool to allow the human to edit a specified Headspace config. Only pass the name of the headsapce. """

        if headspace_name.lower() not in self.headspaces:
            return agent_observation(f"Headspace: {headspace_name} cannot be found in availible headspaces: {self.headspaces}")

        qr_code_url = f"http://{get_network_url()}/config_edit/{headspace_name}"
        qr_path = generate_qr_image(qr_code_url)

        self.dialog.visual = qr_path

        return agent_observation(f"Finished! Here is a QR code the Human can use to edit the {headspace_name} config. The URL is {qr_code_url}")

