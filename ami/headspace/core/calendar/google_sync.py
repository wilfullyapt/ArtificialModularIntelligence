from pathlib import Path
from datetime import datetime

from typing import Union, List

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from ami.base import Base
from ami.headspace.core.calendar.cal_config import CalendarConfig
from ami.headspace.core.calendar.common import DateRange, Event


class GoogleAuth(Base):
    def __init__(self, save_dir: Path):
        super().__init__()
        self._service = None

        save_dir.mkdir(parents=True, exist_ok=True)

        self.credentials = None
        self.token_path = save_dir / "token.json"
        self.credentials_path = save_dir / "credentials.json"

        self.calconf = CalendarConfig()
#       calendar_filepath = save_dir / self.calconf.yaml.get("calendar_filename", "calendar.json")
#       self.calconf = JsonCalendar(calendar_filepath)

        self.SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

    @property
    def user_colors(self):
        return { name: self.calconf.user_colors[i] for i, name in enumerate([ item['summary'] for item in self.get_available_calendars() ]) }

    @property
    def service(self) -> Resource:
        if self._service is None:
            try:
                service = build("calendar", "v3", credentials=self.get_credentials())

                if not service._validate_credentials():
                    raise ValueError("Failed to validate Google Calendar service credentials")

                self._service = service

            except HttpError as e:
                print(f"HTTP error occurred: {e}")
            except Exception as e:
                print(f"error occurred: {e}")

        return self._service

    @property
    def credentials_save_path(self):
        return self.credentials_path

    def get_credentials(self):
        creds = None
        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(self.token_path)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())

            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=0)

        with open(self.token_path, "w") as token:
              token.write(creds.to_json())

        return creds

    def get_available_calendars(self):
        try:
            calendar_list = self.service.calendarList().list().execute()
            calendars = calendar_list.get('items', [])
            return [{'id': calendar['id'], 'summary': calendar['summary']} for calendar in calendars]
        except HttpError as e:
            print(f"An error occurred while fetching calendars: {e}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return []

    def _validate_date_format(self, date_string):
        try:
            datetime.fromisoformat(date_string.rstrip('Z'))
            return True
        except ValueError:
            return False

    def _find_calendar_id(self, calendar_input):
        if calendar_input is None or calendar_input.lower() == "primary":
            return "primary"

        for calendar in self.get_available_calendars():
            if calendar_input == calendar['id'] or calendar_input == calendar['summary']:
                return calendar['id']

        raise ValueError(f"No calendar found with ID or summary: {calendar_input}")

    def get_raw_events(self, calendar_id=None, date_range: Union[DateRange,None]=None):
        calendar_id = self._find_calendar_id(calendar_id)

        if date_range is None:
            now = datetime.now()

            #TODO Engineer out the need for the calendar config timezone. Do that here and assign the timezone on the calendar side.
            date_range = DateRange.from_start(start_date=now, timezone=self.calconf.tz)

        from_date = date_range.start.isoformat() + "Z"
        to_date = date_range.end.isoformat() + "Z"

        return self.service.events().list(
            calendarId=calendar_id,
            timeMin=from_date,
            timeMax=to_date,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

    def get_events(self, date_range:Union[DateRange, None]=None) -> List[Event]:
        calendars = [ item['summary'] for item in self.get_available_calendars() ]
        raw_events_dict = { cal_name: self.get_raw_events(calendar_id=cal_name, date_range=date_range)['items'] for cal_name in calendars }
        raw_events_list = [ {**event, 'source': name, 'color': self.user_colors[name] } for name, raw_events in raw_events_dict.items() for event in raw_events  ]
        return [ Event.from_gsync(raw_json) for raw_json in raw_events_list ]

    def is_valid(self):
        if not self.token_path.exists():
            return False
        return self.service._validate_credentials()
