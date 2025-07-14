from typing import Literal, Optional

from ami.headspace import Headspace, ami_tool

class CorespaceHeadspace(Headspace):
    """ Built-in Datetime agent """

    @ami_tool
    def set_reminder(
            self,
            name: str,
            interval: int,
            interval_unit: Literal["hours", "days", "weeks", "months"],
            reoccurring: bool=False
    ):
        """ Set a reminder for something. Unless explicitly stated do not make it reoccurring. """
        return "Reminder successfully set!"

    @ami_tool
    def set_timer(self, number: int, unit: Literal["minutes", "hours"], name: Optional[str]):
        """ Set a timer for something. Only name it if explicitly named by the user. 5 minutes => (5,"minutes"), 2 hours => (2, "hours") """
        return "Timer successfully set!"
