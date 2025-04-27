import os
import qrcode
import yaml
import markdown
from pathlib import Path
from typing import List

from pydantic import BaseModel, Field

from ami.headspace.filesystem import Filesystem
from ami.config import Config
from ami.headspace.base import SharedTool




class Media(SharedTool):
    """ The media Headspace should be able to follow these instructions:
        - "AMI/Raspi, Play the latest video from PotatoMcWhiskey"
        - "AMI/Raspi, Play my oldies playlist from spotify"
        - "AMI/Raspi, Play Rusted from the Rain" :Plays the song only once:
    """

    def __init__(self):
        local_config_path = Path(__file__).parent / "config.yaml"
        with open(local_config_path, "r") as f:
            self.config = yaml.safe_load(f)

        self.filesystem = Filesystem("media")

    def get_youtube_videos(self, creator: str=""):
        pass
