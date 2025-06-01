from typing import List

from ami.headspace import BaseWidgetSettings

class MarkdownDefaultSettings(BaseWidgetSettings):
    relx: float = .5
    rely: float = .4
    anchor: str = "n"
    markdown_files: List[str] = ["effective_accelerationism.md", "techno_optimist.md"]
    background_color: str = "black"
    border: str = "1px solid white"
    font_name: str = "Arial"
    highlight_color: str = "#C3C3C3"
    lowlight_color: str = "#C3C3C3"

    width: int = 300
    height: int = 300
    padding: int = 20

    font: str = "Verdana"
    font_size: int = 12
    h1_size: int = 22
    h2_size: int = 20
    h3_size: int = 18
