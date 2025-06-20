import datetime
from typing import Optional, Union
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

from ami.config import Config
from ami.headspace.core.calendar.cal_config import CalendarConfig

class DateRange(BaseModel):
    start_dt: datetime.datetime
    end_dt: datetime.datetime
    timezone: ZoneInfo = Field(default_factory=lambda: ZoneInfo(Config().get("timezone", "UTC")))

    class Config:
        arbitrary_types_allowed = True

    def as_utc(self, date: datetime.datetime) -> datetime.datetime:
        return date.replace(tzinfo=self.timezone).astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

    @property
    def start(self) -> datetime.datetime:
        return self.as_utc(self.start_dt)
        return self.start_dt

    @start.setter
    def start(self, value: datetime.datetime):
        self.start_dt = value

    @property
    def end(self) -> datetime.datetime:
        return self.end_dt

    @end.setter
    def end(self, value: datetime.datetime):
        self.end_dt = value

    @classmethod
    def from_start(cls, start_date: datetime.datetime, days: int=14, timezone: Union[ZoneInfo,None]=None):
        if start_date.tzinfo and isinstance(start_date.tzinfo, ZoneInfo):
            timezone = start_date.tzinfo
            start_date = start_date.replace(tzinfo=None)
        end_date = start_date + datetime.timedelta(days=days)
        instance = cls(start_dt=start_date, end_dt=end_date)
        if timezone is not None:
            instance.timezone = timezone
        return instance

    @classmethod
    def to_end(cls, end_date: datetime.datetime, days: int=14, timezone: Union[ZoneInfo,None]=None):
        if end_date.tzinfo and isinstance(end_date.tzinfo, ZoneInfo):
            timezone = end_date.tzinfo
            end_date = end_date.replace(tzinfo=None)
        start_date = end_date - datetime.timedelta(days=days)
        instance = cls(start_dt=start_date, end_dt=end_date)
        if timezone is not None:
            instance.timezone = timezone
        return instance

    @property
    def num_days(self) -> int:
        return (self.end_dt - self.start_dt).days

    def __str__(self):
        return f"DateRange(start={self.start}, end={self.end}, timezone={self.timezone})"


class Event(BaseModel):
    name: str = Field(..., description="The name of the Event")
    date: datetime.date = Field(..., description="The date of the event")
    time: Optional[datetime.time] = Field(None, description="Time of the event")
    source: str = Field("JSON", description="This either references the internal JSON calendar or from a sync location")
    color: str = Field(default_factory=lambda: CalendarConfig().color_scheme.default,
                       description="Color of the event to display on the calendar")

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_gsync(cls, json_data):
        default_timezone: ZoneInfo = CalendarConfig().tz
        try:
            is_all_day = False
            event_time = None

            if 'date' in json_data['start']:
                # All-day event
                start = datetime.datetime.fromisoformat(json_data['start']['date'])
                end = datetime.datetime.fromisoformat(json_data['end']['date'])
                is_all_day = True
            elif 'dateTime' in json_data['start']:
                # Event with specific time
                start_tz = ZoneInfo(json_data['start'].get('timeZone', default_timezone.key))
                end_tz = ZoneInfo(json_data['end'].get('timeZone', default_timezone.key))

                start = datetime.datetime.fromisoformat(json_data['start']['dateTime']).replace(tzinfo=start_tz)
                end = datetime.datetime.fromisoformat(json_data['end']['dateTime']).replace(tzinfo=end_tz)

                # Check if it's a 24-hour event (potential all-day event)
                if (end - start) == datetime.timedelta(days=1):
                    is_all_day = True
                else:
                    event_time = start.astimezone(default_timezone).time()
            else:
                raise ValueError("Invalid 'start' format in event data")

            return cls(
                name=json_data['summary'],
                date=start.astimezone(default_timezone).date(),
                time=event_time,
                source=json_data['source'],
                color=json_data['color']
            )

        except Exception as e:
            print(f"Error in converting the json event: {e}")
            print(json_data)
            return None

    @classmethod
    def from_local_json(cls, date: str, name: str, time: str):
        try:
            time = datetime.datetime.strptime(time, "%H:%M").time()
        except:
            time = None
        return cls(name=name, date=datetime.datetime.fromisoformat(date).date(), time=time)

