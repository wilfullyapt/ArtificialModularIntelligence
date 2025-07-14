from ami.headspace import BaseWidgetSettings

class CorespaceDefaultSettings(BaseWidgetSettings):
    x: int = 1
    y: int = 1
    anchor: str = "nw"
    background_color: str = "black"
    font_name: str = "Helvetica"
    highlight_color: str = "#C34456"
    lowlight_color: str = "#331111"
