import re
from datetime import datetime, timedelta

from langchain_core.prompts import PromptTemplate

from ami.flask.manager import get_network_url
from ami.headspace import Headspace, ami_tool
#from ami.headspace import Headspace, ami_tool, agent_observation
from ami.headspace.core.calendar.google_sync import GoogleAuth
from ami.headspace.headspace import generate_qr_image

from .json_calendar import JsonCalendar, Event

INFER_DATE_PROMPT = """Your goal is to infer what the user meant when they said '{user_input}'. You should only respond with only YYYY-MM-DD and nothing else.
The user is only thinking about future dates, unless otherwise specifically stated.
For example, if the user says 'the first' or 'the 1st' and its the 15th, the user means the first of next month. Only consider future dates in context to what the user says.
Known: {dates}.
You should only respond with a 'YYYY-MM-DD format' and nothing else. Reminder that today is {date_string}
What do you think the user meant by '{user_input}' from the perspective of {date_string}?
"""

class Calendar(Headspace):
    """ Built-in calendar agent """

    HANDLE_PARSING_ERRORS: bool = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        calendar_filepath = self.filesystem / self.yaml.get("calendar_filename", "calendar.json")
        self.cal = JsonCalendar(calendar_filepath)
        self.auth = GoogleAuth(self.filesystem.path)

    def verbose_date(self, date_str):
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%A, %B %d")

    def remove_quotes(self, string):
        return string.strip("' \"")

    @ami_tool
    def get_calendar(self):
        """ Return the contents of the calendar """
        return str(self.cal._json)

    @ami_tool
    def get_date_events(self, date: str):
        """ Given a date (YYYY-MM-DD), return an list of events. Use if you don't know the name of an event. """
        try:
            events = self.cal[date]
        except:
            return { "invalid input": "Input date string does not match `YYYY-MM-DD` format!"}
        if not events:
            return None
        return {"return": events}

    @ami_tool
    def add_event(self, date: str, name: str):#, **kwargs):
        """ Given a date (YYYY-MM-DD) and a name, return an Event.""" # Details are optional but can inclue 'time' or 'location' or 'reoccurring'"""

        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return "Incorrect format! Date must be a 'YYYY-MM-DD' pattern."
#           return agent_observation("Incorrect format! Date must be a 'YYYY-MM-DD' pattern.")

        event = Event(date=date, name=name.capitalize())#, **kwargs)

        try:
            self.cal.save(events=[event])
        except ValueError as e:
            return f"Add Event({event.to_json()}) Completed Successfully!!"
#           return agent_observation(f"Add Event({event.to_json()}) Completed Successfully!!")

        return f"Add Event({event.to_json()}) Completed Successfully!!"
#       return agent_observation(f"Add Event({event.to_json()}) Completed Successfully!!")

    @ami_tool
    def remove_event(self, date: str, name: str):
        """ Remove an event from the calendar given a date and a name for the event to be removed """

        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return "Incorrect format! Date must be a 'YYYY-MM-DD' pattern."
#           return agent_observation("Incorrect format! Date must be a 'YYYY-MM-DD' pattern.")

        if name == "*":
            names = [ event.name for event in self.cal.get_date(date) ]
        else:
            names = [name]

        try:
            result = [ self.cal.remove_event(self.cal[date, n], agent_return=True) for n in names ]
        except Exception as e:
            return f"Event '{names}' not found for Date({date}) | {e}"
#           return agent_observation(f"Event '{names}' not found for Date({date}) | {e}")

        if result:
            return f"Remove Event Completed Successfully! result: {result}"
#           return agent_observation(f"Remove Event Completed Successfully! result: {result}")
        else:
            return "Remove Event Failed!"
#           return agent_observation("Remove Event Failed!")

    @ami_tool
    def update_event(self, date: str, event_name: str, details: dict = {}):
        """ Given a date (YYYY-MM-DD) and event name, update the event to match the details dictionary """

        # This is the part where the fields are offered to the user to change
        # How can you take an Event as a Form and mix and match via the LLM?
        # How can you gain clarification from the user if the fields are unclear

        event = self.cal[date, event_name]
        event_details.to_dict()
        if not details:
            details = self.get_human_feedback("What details would you like to change?", event_details)

        for key, value in details:
            event_details[key] = value

        new_event = Event(**details)
        result = self.cal.modify_event(event, new_event, save_events=True, agent_return=True)

        return result

    @ami_tool
    def comprehend_date(self, user_input: str):
        """
        Always use this tool to translate natural language into a usable date string since you don't know what day it is.
        user_input is the relitive context for the target date (e.g. 'the first' or 'friday' or 'next tuesday').
        """
        def date_lookahead(weeks, start_date):
            dates = []

            for  i in range(0, weeks * 7):
                day  = (start_date + timedelta(days=i)).strftime("%A")
                date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")

                if i == 0:
                    dates.append((f"Tomorrow, This {day}", date))
                elif i > 0 and i < 6:
                    dates.append((f"This {day}", date))
                elif i >= 6 and i < 13:
                    dates.append((f"Next {day}", date))
                elif i >= 13 and i < 20:
                    dates.append((f"Following {day}", date))
                else:
                    dates.append((day, date))

            return dates

        today_date = datetime.now() 
        week_lookahead = 3
        dates = [(f"Today, {today_date.strftime('%A')}", today_date.strftime("%Y-%m-%d"))] + date_lookahead(week_lookahead+1, today_date+timedelta(days=1))
        date_string = f"{today_date.strftime('%A')} {today_date.day} {today_date.strftime('%B')}"

        infer_date_prompt = PromptTemplate.from_template(INFER_DATE_PROMPT)
        result = self.spawn_llm().invoke(infer_date_prompt.format(user_input=user_input, dates=dates, date_string=date_string), stop=[".", "\n"])

        match = re.search(r'\b\d{4}-\d{2}-\d{2}\b', result)
        if match:
            return f"The user means: {match.group()}"
#           return agent_observation(f"The user means: {match.group()}")

        return result

    @ami_tool
    def sync_with_google(self):
        """ Use this tool to sync the calendar with the Human's Google calendar """

        qr_code_url = f"http://{get_network_url()}/sync_google"
        qr_path = generate_qr_image(qr_code_url)

        self.dialog.visual = qr_path
        return f"Finished! Here is a QR code to sync a google calendar. {qr_code_url}"
#       return agent_observation(f"Finished! Here is a QR code to sync a google calendar. {qr_code_url}")

    @ami_tool
    def add_reoccurring_event(self, name: str, details: dict={}):
        """ Add an event to the calendar with reoccurring conditionals """
        return "Calendar.add_reoccurring_event has not been implemented! Bad tool!"
#       return agent_observation("Calendar.add_reoccurring_event has not been implemented! Bad tool!")

    @ami_tool
    def add_celebration(self, name: str, inception: str):
        """ Add an annual event to the calendar that happends once a year from a starting point """
        return "Calendar.add_celebration has not been implemented! Bad tool!"
        return agent_observation("Calendar.add_celebration has not been implemented! Bad tool!")
