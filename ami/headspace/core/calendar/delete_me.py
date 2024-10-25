from flask import Flask, request, jsonify, session
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# This should be off in production
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

@app.route('/')
def index():
    return '''
    <h1>Local Calendar Access</h1>
    <button onclick="initiateAuth()">Allow Calendar Access</button>
    <div id="auth_instructions" style="display:none;">
        <p>To authorize access to your calendar, please follow these steps:</p>
        <ol>
            <li>Click the link below to open Google's authorization page</li>
            <li>Log in and grant access to your calendar</li>
            <li>Copy the authorization code from the resulting page</li>
            <li>Paste the code in the input field below and click submit</li>
        </ol>
        <a id="auth_url" href="#" target="_blank">Open Google Authorization</a>
        <br><br>
        <input type="text" id="auth_code" placeholder="Enter authorization code">
        <button onclick="submitAuthCode()">Submit Code</button>
    </div>
    <div id="events"></div>
    <script>
    function initiateAuth() {
        fetch('/initiate_auth')
            .then(response => response.json())
            .then(data => {
                document.getElementById('auth_instructions').style.display = 'block';
                document.getElementById('auth_url').href = data.auth_url;
            });
    }
    function submitAuthCode() {
        const code = document.getElementById('auth_code').value;
        fetch('/submit_auth_code', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({code: code}),
        })
        .then(response => response.json())
        .then(data => {
            if (data.events) {
                displayEvents(data.events);
            } else {
                alert('Authentication failed. Please try again.');
            }
        });
    }
    function displayEvents(events) {
        document.getElementById('auth_instructions').style.display = 'none';
        document.getElementById('events').innerHTML = 
            '<h2>Upcoming Events:</h2>' + 
            events.map(event => `<p>${event.summary}: ${event.start.dateTime || event.start.date}</p>`).join('');
    }
    </script>
    '''

@app.route('/initiate_auth')
def initiate_auth():
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": "YOUR_APP_NAME",
                "client_secret": "YOUR_APP_SECRET",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"]
            }
        },
        SCOPES
    )
    auth_url, _ = flow.authorization_url(prompt='consent')
    session['flow'] = flow
    return jsonify({'auth_url': auth_url})

@app.route('/submit_auth_code', methods=['POST'])
def submit_auth_code():
    code = request.json.get('code')
    flow = session.get('flow')
    if not flow:
        return jsonify({'error': 'No active authentication flow'}), 400

    flow.fetch_token(code=code)
    credentials = flow.credentials
    
    service = build('calendar', 'v3', credentials=credentials)
    events_result = service.events().list(calendarId='primary', maxResults=10,
                                          singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])
    
    session['credentials'] = credentials_to_dict(credentials)
    return jsonify({'events': events})

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
