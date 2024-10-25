""" AMI Core Headspace Blueprint for Calendar """

import os
import secrets
import json
import pickle
from pathlib import Path
import datetime

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError

from flask import request, jsonify

from ami.base import Base
from ami.headspace.blueprint import Blueprint, HeaderButton, route, render_template
#from .credentials_google import GoogleCredentials

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


class GoogleAuth(Base):
    def __init__(self, save_dir: Path):
        super().__init__()
        save_dir.mkdir(parents=True, exist_ok=True)
        self.token_path = save_dir / "token.json"
        self.credentials_path = save_dir / "credentials.json"
        self.credentials = None

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
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
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

    def get_events(self):
        return self.get_base_service().events().list(
            calendarId="primary",
            timeMin=datetime.datetime.utcnow().isoformat() + "Z",  # 'Z' indicates UTC time
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

    def validate(self):
        if not self.token_path.exists():
            return False
        return self.get_base_service()._validate_credentials()

class Calendar(Blueprint):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_tempsets(css='sync.css')

        self.creds = GoogleAuth(self.filesystem.path)
        self.logs.info(f"Calendar blueprint initialized with credentials path: {self.creds_path}")

    @route('/sync_google')
    def sync_google(self):
        """Landing page with instructions for users"""
        return render_template(
            'sync_google.html',
            tempsets=self.tempsets.augment(
                header="Set Up Google Calendar Access"
            )
        )

    @route('/setup_instructions')
    def setup_instructions(self):
        """Provides instructions for users to set up their own credentials"""
        instructions = {
            'steps': [
                "Go to <a href='https://console.cloud.google.com/'>Google Cloud Console</a>",
                "Create a new project (or select an existing one)",
                "Enable the Google Calendar API for your project",
                "Go to Credentials → Create Credentials → OAuth Client ID",
                "Choose 'Desktop Application' as the application type",
                "Download the credentials JSON file",
                "Save it as 'desktop_client_secret.json' in this application's config directory",
                "Click 'Start Authorization' below once complete"
            ],
            'next_step': '/initiate_auth'
        }
        return jsonify(instructions)

    @route('/auth_status')
    def auth_status(self):
        """Check if user is currently authorized"""
        try:
            return jsonify({'authorized': self.creds.validate()})

        except Exception as e:
            return jsonify({
                'authorized': False,
                'error': str(e)
            })

    @route('/upload_google_credentials', methods=['POST'])
    def upload_google_credentials(self):
        try:
            if 'credentials' not in request.files:
                return jsonify({'success': False, 'message': 'No file part in the request'}), 400

            file = request.files['credentials']

            if file.filename == '':
                return jsonify({'error': 'No file selected for uploading'}), 400

            if file:
                file.save(self.creds.credentials_save_path)
                return jsonify({'success': True, 'message': 'Credentials uploaded successfully'}), 200

        except Exception as e:
            self.logs.error(f"Error uploading credentials: {str(e)}")
            return jsonify({'error': f'Failed to upload credentials: {str(e)}'}), 500

    @route('/initiate_auth', methods=['GET','POST'])
    def initiate_auth(self):
        """Initiates the OAuth flow using the user's credentials"""
        try:
            creds = self.creds.get_credentials()

            if not creds:
                return jsonify({
                    'error': 'Client secret file not found',
                    'message': 'Please complete the setup instructions first'
                }), 404

            return jsonify({
                'success': True,
                'message': 'Authorization successful! You can now access your calendar.'
            })

        except Exception as e:
            return jsonify({
                'error': str(e),
                'message': 'Authorization failed. Find another way to attempt this. Good luck.'
            }), 400

    @route('/list_events')
    def list_events(self):
        """Lists calendar events using stored credentials"""
        try:
            if not self.creds_path.exists():
                return jsonify({
                    'error': 'Not authorized',
                    'message': 'Please complete authorization first'
                }), 401

            with open(self.creds_path, 'r') as token:
                creds = Credentials.from_authorized_user_file(
                    self.creds_path, SCOPES)

            if not creds.valid:
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    return jsonify({
                        'error': 'Invalid credentials',
                        'message': 'Please reauthorize'
                    }), 401

            service = build('calendar', 'v3', credentials=creds)
            events_result = service.events().list(
                calendarId='primary',
                maxResults=10,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            return jsonify({'events': events})

        except Exception as e:
            return jsonify({
                'error': str(e),
                'message': 'Failed to fetch events'
            }), 400
