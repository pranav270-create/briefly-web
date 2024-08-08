from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from typing import Optional
import os, base64, re


CREDENTIALS = "./gmail_other.json"
TOKEN = "./token_other.json"
SCOPES = [
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]


def get_google_api_service(service_name: str, version: str, token: Optional[str] = None):
    if token is not None:
        creds = Credentials(token=token, scopes=SCOPES)
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                raise ValueError("Invalid credentials")
        return build(service_name, version, credentials=creds)
    else:
        creds = None
        if os.path.exists(TOKEN):
            creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS, SCOPES)
                creds = flow.run_local_server(port=0)
            assert (creds) is not None, "No GMAIL credientals found"
            with open(TOKEN, 'w') as token:
                token.write(creds.to_json())
        return build(service_name, version, credentials=creds)