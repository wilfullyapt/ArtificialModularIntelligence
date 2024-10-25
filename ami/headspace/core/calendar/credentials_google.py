import os
import pickle
from pathlib import Path
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

class GoogleCredentials:
    def __init__(self, token_file_path: Path):
        self.token_file_path = token_file_path
        self.credentials = None

    def load_credentials(self):
        if os.path.exists(self.token_file_path):
            with open(self.token_file_path, 'rb') as token:
                self.credentials = pickle.load(token)

        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
            else:
                flow = Flow.from_client_secrets_file(
                    'path/to/client_secrets.json',
                    scopes=['https://www.googleapis.com/auth/calendar.readonly']
                )
                self.credentials = flow.run_local_server(port=0)

            self.save_credentials()

    def save_credentials(self):
        with open(self.token_file_path, 'wb') as token:
            pickle.dump(self.credentials, token)

    def get_credentials(self):
        if not self.credentials:
            self.load_credentials()
        return self.credentials

