
import json
import shutil
import datetime
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from pydantic import BaseModel, Field, field_validator, field_serializer

from ami.headspace.base import SharedTool
from ami.headspace.core.calendar.common import Event as CommonEvent

# ------------------------------------------------------------------------
# homeai.flask.utils.py AND homeai.flask.flask_server.py use this script
# ------------------------------------------------------------------------

# ------------------------------------------------------------------------
#                 Enums

class CalendarResolution(Enum):
    WEEK = 1
    MONTH = 2
    DAY = 3

class Reoccurring(Enum):
    """ The Reoccurring Enum dictates.
        These plain text Enums dicate in the Calendar class how to intrupret and use reoccurring events.

        ANNUAL: Same day every year.
        BIWEEKLY: +14 days
        MONTHLY: Same day of the month
        MONTHLY_DOW: Day of week relitive to the month. First Saturday or second Teusday... etc

    """
    WEEKLY = "WEEKLY"
    BIWEEKLY = "BIWEEKLY"
    MONTHLY = "MONTHLY"
    MONTHLY_DOW = "MONTHLY_DOW"

# -----------------------------------------------------------------
#                 Functions

def underscore_json_keys(input_dict):
    result = { f"_{key}": value for key, value in input_dict.items() }
    return result

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + datetime.timedelta(n)

def list_enum_values(enum_class):
    return [member.value for member in enum_class]

# -----------------------------------------------------------------
#                 Classes

class Event(BaseModel):
    date: datetime.date = Field(None, description="Date as a 'YYYY-MM-DD' string")
    name: str = Field(None, description="The name of the Event")
    time: Optional[datetime.time] = Field(None, description="Time string as a 'HH:MM' string")
    reoccurring: Optional[Reoccurring] = Field(None, description=f"Possible string inputs: {list_enum_values(Reoccurring)}")
    location: Optional[str] = Field(None, description="The location as a string")
    color: Optional[str] = Field(None, description="Only if know, the color as a hex string")

    class Config:
        arbitrary_types_allowed=True

    @field_validator('date', mode='before')
    def parse_date(cls, v):
        if isinstance(v, str):
            try:
                return datetime.datetime.strptime(v, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError('Date must be in the format "YYYY-MM-DD"')
        if isinstance(v, datetime.datetime):
            return v.date()
        return v

    @field_validator('time', mode='before')
    def parse_time(cls, v):
        if v == "None": v = None
        if isinstance(v, str):
            try:
                return datetime.datetime.strptime(v, '%H:%M').time()
            except ValueError:
                raise ValueError('Time must be in the format "HH:MM"')
        if isinstance(v, datetime.datetime):
            return v.time()
        return v

    @field_validator('reoccurring')
    def validate_reoccurring(cls, v):
        if v not in Reoccurring:
            raise ValueError(f"Possible Reoccurring values are only: {list_enum_values(Reoccurring)}")
        return v

    @property
    def date_str(self):
        return str(self.date)

    @property
    def time_str(self):
        return str(self.time)

    @property
    def next(self):
        if not self.reoccurring:
            print("Event.next: False Start")
            return None

        serialized_event = self.dump()

        if self.reoccurring is Reoccurring.WEEKLY:
            serialized_event['date'] = str(self.date + datetime.timedelta(days=7))

        elif self.reoccurring is Reoccurring.BIWEEKLY:
            serialized_event['date'] = str(self.date + datetime.timedelta(days=14))

        elif self.reoccurring is Reoccurring.MONTHLY:
            next_month = self.date.month + 1
            next_year = self.date.year
            if next_month > 12:
                next_month = 1
                next_year += 1
            serialized_event['date'] = f"{next_year}-{next_month:02d}-{self.date.day:02d}"

        elif self.reoccurring is Reoccurring.MONTHLY_DOW:
            first_day_of_month = (self.date.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)
            first_occurrence = first_day_of_month + datetime.timedelta(days=(self.date.weekday() - first_day_of_month.weekday()) % 7)
            week_number = (self.date.day - 1) // 7 + 1
            next_occurrence = first_occurrence + datetime.timedelta(days=(week_number - 1) * 7)
            serialized_event['date'] = str(next_occurrence)

        return Event(**serialized_event)

    @property
    def prev(self):
        if not self.reoccurring:
            print("Event.prev: False Start")
            return None

        serialized_event = self.dump()

        if self.reoccurring is Reoccurring.WEEKLY:
            serialized_event['date'] = str(self.date - datetime.timedelta(days=7))

        elif self.reoccurring is Reoccurring.BIWEEKLY:
            serialized_event['date'] = str(self.date - datetime.timedelta(days=14))

        elif self.reoccurring is Reoccurring.MONTHLY:
            prev_month = self.date.month - 1
            prev_year = self.date.year
            if prev_month < 1:
                prev_month = 12
                prev_year -= 1
            serialized_event['date'] = f"{prev_year}-{prev_month:02d}-{self.date.day:02d}"

        elif self.reoccurring is Reoccurring.MONTHLY_DOW:
            first_day_of_month = (self.date.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
            first_occurrence = first_day_of_month + datetime.timedelta(days=(self.date.weekday() - first_day_of_month.weekday()) % 7)
            week_number = (self.date.day - 1) // 7 + 1
            next_occurrence = first_occurrence + datetime.timedelta(days=(week_number - 1) * 7)
            serialized_event['date'] = str(next_occurrence)

        return Event(**serialized_event)

    @field_serializer('date')
    def serialize_date(self, _date: datetime.date):
        if isinstance(_date, datetime.date):
            return str(_date)

    @field_serializer('time')
    def serialize_time(self, _time: datetime.time):
        if isinstance(_time, datetime.time):
            return str(_time)

    @field_serializer('reoccurring')
    def serialize_reoccurring(self, _reoccurring: Reoccurring):
        if isinstance(_reoccurring, Reoccurring):
            return _reoccurring.value

    def dump(self):
        return { key: value for key, value in self.model_dump().items() if value is not None }

    def to_json(self):
        return { "name": self.name, "time": self.time_str }

    def to_dict(self):
        json = self.to_json()
        json["date"] = self.date_str
        return json

@dataclass
class Celebrations:
    json: dict
    events: List[Event] = field(default_factory=list) 

    def __post_init__(self):
        for key, value in self.json.items():
            self.events.append((key, value))

    def __getitem__(self, value):
        pass

    def __contains__(self, value):
        pass

    def __repr__(self):
        return f"Celebrations({len(self.events)} celebrations)"

    @property
    def contents(self):
        return list(self.json.keys())

@dataclass
class Events:
    """ Events lazy loads the json information as Event items or a list of event items given the date_string, "2024-02-13" """
    _json: dict = field(default_factory=dict)
    _events: dict[str, List[Event]] = field(default_factory=dict)

    def __post_init__(self):
        self.json.pop("celebrations", None)

    def __getitem__(self, date_string: str):

        try:
            datetime_object = datetime.datetime.strptime(date_string, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError(f"Events.__getitem__({date_string}) is not a valid date. Must be in 'YYYY-MM-DD' format!")

        if date_string in self.keys:
            return self.events[date_string]

        if date_string[:4] not in self.json:
            return []

        if date_string[5:7] not in self.json[date_string[:4]]:
            return []

        if date_string[-2:] not in self.json[date_string[:4]][date_string[5:7]]:
            return []

        data = self.json[date_string[:4]][date_string[5:7]][date_string[-2:]]
        self.events[date_string] = [ Event(date=date_string, **event_details) for event_details in data ]

        return self.events[date_string]

    def __setitem__(self, date_string, value):
        self.events[date_string] = value

    def __contains__(self, value):
        if self[value] is not None:
            return True
        return False

    @property
    def events(self):
        return self._events

    @property
    def json(self):
        return self._json

    @property
    def keys(self):
        return list( self.events.keys() )

    def append(self, event):
        date = str(event.date)
        if date in self:
            self[date].append(event)
        else:
            self[date] = [event]

    def remove(self, event):
        date = str(event.date)
        if date in self:
            self[date].remove(event)

    def to_json(self):

        if not self.json:

            if not self.events:
                raise ValueError("<Events> object cannot be translated to JSON! No Events in the object!")

            for key, events in self.events.items():
                self.json[key] = [ event.to_json() for event in events  ]

        return self.json

    @classmethod
    def from_events(cls, events_list: list):
        events = cls()
        for event in events_list:
            events.append(event)
        return events.to_json()

    @classmethod
    def from_json(cls, json):
        events = cls()
        events._json = json
        return events

class SaveUnnecessary(Exception):
    pass

class InvalidCalendarKey(Exception):
    pass

class JsonCalendar(SharedTool):

    def __init__(self, calendar_filepath: Path):
        super().__init__()

        self._events: Events | None = None
        self._celebrations = None
        self.calendar_filepath = calendar_filepath

        if self.calendar_filepath.is_file():
            with open(self.calendar_filepath) as f:
                self._json = json.load(f)
        else:
            self._json = {"celebrations": {}}
            today = datetime.datetime.now().date()
            today_you = Event(date=str(today), name="Completed AMI Setup!")
            tomorrow_you_will = Event(date=str(today+datetime.timedelta(days=1)), name="ACCELERATE")
            self.save(events=[today_you, tomorrow_you_will])
#           raise FileNotFoundError(f"File not found: {self.calendar_filepath}")


    def __getitem__(self, key) -> Event | List[Event] | List[str]:
        """
            The Calendar should be indexable mutliple ways:
                  __KEY__              __RETURN__
                - ["date", "event"] -> Event
                - ["date"]          -> List[Event]
                - ["date":"date"]   -> List[str(dates)]

            Returns: List or Event
        """

        if isinstance(key, datetime.date):
            key = str(key)

        # Calendar["2025-01-01", "New Year's"] => Event(date=2025-01-01, name=New Year's)
        if isinstance(key, tuple):
            if len(key) == 2:
                date = key[0]
                event_name = key[1]

                events = self.events[date]
                if events:
                    for event in events:
                        if event.name == event_name:
                            return event

            raise InvalidCalendarKey(f"Invalid key: {key}")

        # Calendar["2025-01-01"] => list[ Event(date=2025-01-01, ...), ... ]
        if isinstance(key, str):
            return self.events[key]

        # Calendar["2024-03-17":"2024-05-23"] => Range of Events from start to end
        if isinstance(key, slice):

            start_date = datetime.datetime.strptime(key.start, "%Y-%m-%d").date()
            end_date = datetime.datetime.strptime(key.stop, "%Y-%m-%d").date()
            return [ date.strftime("%Y-%m-%d") for date in daterange(start_date, end_date) ]

        raise InvalidCalendarKey(f"Invalid key: {key}")

    def __contains__(self, event) -> bool:
        if event is None:
            return False

        if not isinstance(event, Event):
            raise ValueError(f"Calendar.__contains__(value) value must be of type `Event`! type(value) -> {type(event)}")

        if event in self[event.date]:
            return True
        return False

    def load(self):
        self._celebrations = Celebrations(json=self._json["celebrations"])
        self._events = Events(_json=self._json.copy())

    @property
    def events(self) -> Events:
        if self._events is None:
            self.load()
        return self._events

    @property
    def celebrations(self):
        if self._celebrations is None:
            self.load()
        return self._celebrations

    def save(self, **calendar_types):

        if "events" in calendar_types:
            save_necessary = False
            events = calendar_types["events"]
            for event in calendar_types["events"]:

                date = str(event.date)

                print(event)

                if date[:4] not in self._json:
                    self._json[date[:4]] = {}

                if date[5:7] not in self._json[date[:4]]:
                    self._json[date[:4]][date[5:7]] = {}

                if date[-2:] not in self._json[date[:4]][date[5:7]]:
                    self._json[date[:4]][date[5:7]][date[-2:]] = []

                if event not in self:
                    save_necessary = True
                    self.events.append(event)
                    self._json[date[:4]][date[5:7]][date[-2:]].append(event.to_json())

            if not save_necessary:
                raise ValueError(f"Calendar.save unnecessary, events already exist! {calendar_types['events']}")

            with open(self.calendar_filepath, "w") as f:
                json.dump(self._json, f)

            self.logs("Events saved to calendar!")

        if "celebrations" in calendar_types:
            self.logs("save annual celebrations to calendar")

        if "json" in calendar_types:
            # Save with json is the only mechnism for deletion
            # Create a backup first
            shutil.copyfile(self.calendar_filepath, self.calendar_filepath.parent / "calendar_backup.json")

            with open(self.calendar_filepath, "w") as f:
                json.dump(calendar_types["json"], f)

            self._json = calendar_types["json"]

            self.logs("Calendar.save(json_data) finished!")

    def remove_event(self, event, agent_return=False):
        json = self._json.copy()

        if event in self:

            year, month, day = map(str, str(event.date).split('-'))
            json[year][month][day].remove(event.to_json())
            self.events.remove(event)

            if not json[year][month][day]:
                del json[year][month][day]

        else:
            if agent_return:
                return f"'{event.name}' doesn't exist for '{event.date}'!"
            return

        self.save(json=json)

        if agent_return:
            return f"'{event.name}' deleted for '{event.date}'!"

        return

    def modify_event(self, from_event: Event, to_event: Event, save_events=False, agent_return=False):
        rm = self.remove_event({"date":from_event.date, "name":from_event.name}, save_events=save_events)
        add = self.add_events(to_event.to_dict(), save_events=save_events)
        if agent_return and rm and add:
            return True
        return

    def log(self, msg, error=False):
        print(f" ::> {msg}")

    def get_date(self, date, propagate_reoccurring=False) -> List[Event]:
        events = self[date]

        if propagate_reoccurring:
            for event in events:
                if event.reoccurring:
                    next_event = event.next
                    if not self[str(next_event.date), next_event.name]:
                        self.save(events=[next_event])

        return events

    def inflate_calendar(self, dates_list: List[str]) -> Dict[str, list]:
        calendar = { date: self.get_date(date, propagate_reoccurring=True) for date in dates_list }
        calendar = { date : [ event.to_json() for event in calendar[date] ] for date in calendar.keys() }
        return calendar


    def inflate_calendar_events(self, dates_list: List[str]) -> Dict[str, List[CommonEvent]]:
        calendar = { date: self.get_date(date, propagate_reoccurring=True) for date in dates_list }
        calendar = { date : [ CommonEvent.from_local_json(date, **event.to_json()) for event in calendar[date] ] for date in calendar.keys() }
        return calendar

