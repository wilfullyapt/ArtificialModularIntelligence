from typing import List
import yaml
from pathlib import Path
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field

from ami.config import Config

class ColorScheme(BaseModel):
    active: str = Field('#666666', description="Color for the active day")
    inactive: str = Field('#C3C3C3', description="Color for the inactive days")
    border: str = Field('#FFD700', description="Color for the day panel borders")
    background: str = Field('#E6F3FF', description="Color for the day panel background")
    default: str = Field('#E69A28', description="Default color for JSON based calendar events")
    one: str = Field("#98FB98", description="Color for the first owner's events")
    two: str = Field("#FFB6C1", description="Color for the second owner's events")
    three: str = Field("#4169E1", description="Color for the third owner's events")
    four: str = Field("#FFA07A", description="Color for the fourth owner's events")
    five: str = Field("#9ACD32", description="Color for the fifth owner's events")
    six: str = Field("#DAA520", description="Color for the sixth owner's events")
    seven: str = Field("#8A2BE2", description="Color for the seventh owner's events")
    eight: str = Field("#BC8F8F", description="Color for the eighth owner's events")

    @property
    def colors(self):
        return [self.one, self.two, self.three, self.four, self.five, self.six, self.seven, self.eight]

class CalendarConfig:
    google_sync: bool
    config_filepath: Path

    def __init__(self):
        """ Hold the calendar configuration """

        config = Config()
        self._timezone = ZoneInfo(config.get("timezone","UTC"))
        config_filepath = config.headspaces_dir / Path(__file__).parent.name / "config.yaml"

        if config_filepath.exists() and config_filepath.is_file():
            with open(config_filepath, 'r') as file:
                yaml_data = yaml.safe_load(file)
            self._validate_yaml_data(yaml_data)
            self._yaml_data = yaml_data
        else:
            raise FileNotFoundError(f"Config file not found or is not a file: {config_filepath}")

        self._fullmode = self._yaml_data.get("calendar_mode", "3-week")
        if self._fullmode.lower() not in ['1-week', '2-week', '3-week', '4-week', '1-day', '2-day', '3-day']:
            self._fullmode = '3-week'

        self._dimensions = self._yaml_data['dimensions'][self._fullmode.split('-')[-1]]
        self._google_sync = bool(self._yaml_data.get('google_sync', False))
        self.color_scheme = ColorScheme(**self._yaml_data.get('colors',{}))
        self._font = self._yaml_data.get('font', 'Verdana')
        self._font_size = self._yaml_data.get('font-size', 8)

    @property
    def yaml(self) -> dict:
        return self._yaml_data
    @property
    def mode(self) -> str:
        return self._fullmode[2:].lower()
    @property
    def height(self) -> int:
        return self._dimensions['height']
    @property
    def width(self) -> int:
        return self._dimensions['width']
    @property
    def tz(self) -> ZoneInfo:
        return self._timezone
    @property
    def g_synced(self) -> bool:
        return self._google_sync
    @property
    def font(self) -> str:
        return self._font
    @property
    def font_size(self) -> int:
        return self._font_size

    @property
    def user_colors(self) -> List[str]:
        return self.color_scheme.colors

    @property
    def days(self) -> int:
        coefficient = { 'week':7, 'day':1 }[self.mode]      # determine the coefficient
        return int(self._fullmode[0]) * coefficient         # the unit as an int * the coefficient

    def _validate_yaml_data(self, yaml_data: dict):
        required_keys = ['calendar_mode', 'dimensions']
        for key in required_keys:
            if key not in yaml_data:
                raise ValueError(f"Missing required key in YAML data: {key}")

        if 'week' not in yaml_data['dimensions'] or 'day' not in yaml_data['dimensions']:
            raise ValueError("Missing 'week' or 'day' in dimensions")

        for unit in ['week', 'day']:
            if 'width' not in yaml_data['dimensions'][unit] or 'height' not in yaml_data['dimensions'][unit]:
                raise ValueError(f"Missing 'width' or 'height' in dimensions for {unit}")
