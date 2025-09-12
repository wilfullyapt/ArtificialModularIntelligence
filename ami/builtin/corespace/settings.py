from typing import List, Tuple

from pydantic import Field

from ami.headspace.settings import BaseWidgetSettings

class CorespaceSettings(BaseWidgetSettings):
    """Settings for the corespace plugin"""

    x: int = 1
    y: int = 1
    anchor: str = "nw"
    background_color: str = "black"
    font_name: str = "Helvetica"
    highlight_color: str = "#decbb3"
    lowlight_color: str = "#ffffff"
    
    reminder_files: List[str] = Field(
        default=["reminders.md"],
        description="List of markdown files to store reminders"
    )
    
    notification_threshold_hours: int = Field(
        default=2,
        description="Hours before reminder when notification should appear"
    )
    
    reminder_background_color: str = Field(
        default="#ff8c00",  # Dark orange/burnt yellow
        description="Background color for urgent reminders"
    )
    
    notification_border: str = Field(
        default="1px solid #333",
        description="Border style for the widget"
    )
    
    font_family: str = Field(
        default="Arial, sans-serif",
        description="Font family for text"
    )
    
    font_size: int = Field(
        default=12,
        description="Font size in pixels"
    )
    
    polling_interval_seconds: int = Field(
        default=60,
        description="How often to check for reminders in seconds"
    )
    
    menu_items: List[Tuple[str, str]] = [
        ("Dashboard", "dashboard"),
        ("System", "system"), 
        ("Plugins", "plugins"),
        ("Reminders", "reminders")
    ]
