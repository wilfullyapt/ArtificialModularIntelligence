from pathlib import Path
from datetime import datetime, timezone

from zoneinfo import ZoneInfo

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from ami.base import Base
from ami.config import Config

class GoogleAuth(Base):
    def __init__(self, save_dir: Path):
        super().__init__()
        save_dir.mkdir(parents=True, exist_ok=True)
        self.token_path = save_dir / "token.json"
        self.credentials_path = save_dir / "credentials.json"
        self.credentials = None
        self.SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

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

    def get_base_service(self):
        creds = self.get_credentials()
        try:
            service = build("calendar", "v3", credentials=creds)
            return service

        except HttpError as e:
            print(f"HTTP error occurred: {e}")
        except Exception as e:
            print(f"error occurred: {e}")

    def _validate_date_format(self, date_string):
        try:
            datetime.fromisoformat(date_string.rstrip('Z'))
            return True
        except ValueError:
            return False

    def get_utc(self, date=None):
        tz = ZoneInfo(Config().get("timezone"))     # timezone object for "America/Los_Angeles"
        if date:
            try:
                parsed_date = datetime.strptime(date, "%Y-%m-%d")
                target_datetime = datetime.combine(parsed_date.date(), datetime.min.time()).replace(tzinfo=tz)
            except ValueError:
                raise ValueError("Invalid date format. Please use 'yyyy-mm-dd'.")
        else:
            target_datetime = datetime.now(tz)

        return target_datetime.astimezone(timezone.utc).replace(tzinfo=None)

    def _find_calendar_id(self, calendar_input):
        if calendar_input is None or calendar_input.lower() == "primary":
            return "primary"

        available_calendars = self.get_available_calendars()
        for calendar in available_calendars:
            if calendar_input == calendar['id'] or calendar_input == calendar['summary']:
                return calendar['id']

        raise ValueError(f"No calendar found with ID or summary: {calendar_input}")

    def get_events(self, calendar_id=None, from_date=None):
        calendar_id = self._find_calendar_id(calendar_id)

        if from_date is None:
            from_date = f"{datetime.now(timezone.utc)}Z"
        elif not self._validate_date_format(from_date):
            raise ValueError("Invalid date format. Please use ISO format with 'Z' suffix (e.g., '2023-05-18T10:00:00Z')")

        return self.get_base_service().events().list(
            calendarId=calendar_id,
            timeMin=from_date,
#           timeMax=to_date,
            maxResults=21,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

    def get_available_calendars(self):
        try:
            service = self.get_base_service()
            calendar_list = service.calendarList().list().execute()
            calendars = calendar_list.get('items', [])
            return [{'id': calendar['id'], 'summary': calendar['summary']} for calendar in calendars]
        except HttpError as e:
            print(f"An error occurred while fetching calendars: {e}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return []

    def is_valid(self):
        if not self.token_path.exists():
            return False
        return self.get_base_service()._validate_credentials()
