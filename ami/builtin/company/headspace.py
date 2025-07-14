from typing import Literal, Optional

from ami.headspace import Headspace, ami_tool
from ami.headspace import HeadspaceInstruction


ANALYSIS_PROMPT = """You are a helpful advisor to your human. Your job is to analyze conversations and documentation to better inform your human about their life and what they should do.
Given all this information, think about their intent towards their future and the actions they are taking in the present. You goal is to contextulize their life.

## Conversation History

## Documented Goals

## Finacial Records


# How to respond
- Be empathetic and understanding to their plight
- When it comes to hard truths, do not pull any punches
- Provide extreme clarity

1. Outline 


"""

#              --== Prompt Divider

UPDATE_GOALS_PROMPT = """You are a helpful AI that updates the set goals for a person.

You are limited to ONE action only.
Tool:
- `append_goal` (goal: str) -> gets appended to the bottom of the Goals list
- `update_goal` (line_number: int, goal: str) -> update the line number to the new goal arguement
- `switch_priorities` (switch_one: int, switch_two: int) -> switch the two lines with each other

# Goals Document

# User Input

"""

class CompanyHeadspace(Headspace):
    """ Built-in Datetime agent """

    @ami_tool
    def company_sentiment_anaylsis(self) -> HeadspaceInstruction:

#       return HeadspaceInstruction.popup_injection(f"{self.name}:company_analysis")
        return HeadspaceInstruction.popup_markdown("path/to/markdown/file")

    @ami_tool
    def input_goal(self, goal: str):
        """ Input a goal to update the set company goals """
        return "Timer successfully set!"
