from typing import Literal, Optional
from urllib.parse import quote_plus

from ami.headspace import Headspace, ami_tool

AGENT_ROLE = """
remove_event(date: str, name: str) - Remove an event from the calendar given a date and a name for the event to be removed, args: {'date': {'title': 'Date', 'type': 'string'}, 'name': {'title': 'Name', 'type': 'string'}}
update_event(date: str, event_name: str, details: dict = {}) - Given a date (YYYY-MM-DD) and event name, update the event to match the details dictionary, args: {'date': {'title': 'Date', 'type': 'string'}, 'event_name': {'title': 'Event Name', 'type': 'string'}, 'details': {'title': 'Details', 'default': {}, 'type': 'object'}}
"""


class DatetimeHeadspace(Headspace):
    """ Built-in Datetime agent """

    HANDLE_PARSING_ERRORS: bool = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def agent_role(self):
        return "This is an agent that governs timing and reminders"

    @ami_tool
    def set_reminder(
            self,
            name: str,
            interval: int,
            interval_unit: Literal["hours", "days", "weeks", "months"],
            reoccurring: bool=False
    ):
        """ Set a reminder for something. Unless explicitly state do not make it reoccurring. """
        return "Reminder successfully set!"

    @ami_tool
    def set_timer(self, number: int, unit: Literal["minutes", "hours"], name: Optional[str]):
        """ Set a timer for something. Only name it if explicitly named by the user. 5 minutes => (5,"minutes"), 2 hours => (2, "hours") """
        return "Timer successfully set!"
