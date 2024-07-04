from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request


def get_google_api_service(service_name: str, version: str, access_token: str):
    SCOPES = ["https://mail.google.com/", "https://www.googleapis.com/auth/calendar"]
    creds = Credentials(token=access_token, scopes=SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise ValueError("Invalid credentials")
    return build(service_name, version, credentials=creds)
