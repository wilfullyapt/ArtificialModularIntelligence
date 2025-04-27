from ami.headspace import Headspace, ami_tool, agent_observation

from .tool import Media as MediaTool

class Media(Headspace):
    """ Built-in markdown agent """

    HANDLE_PARSING_ERRORS: bool = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.media = MediaTool()

    @ami_tool
    def list_videos_from_youtube_creator(self, creator: str):
        """ Use this tool to list out the known markdown files """
        return agent_observation(str(self.media.get_youtube_videos(creator)))

