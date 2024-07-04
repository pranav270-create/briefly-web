import os, base64, re
from typing import List, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from collections import defaultdict


CREDENTIALS = "C:/Users/marka/fun/briefly/backend/integrations/markacastellano2@gmail_credentials_desktop.json"
TOKEN = "C:/Users/marka/fun/briefly/backend/integrations/token.json"

class GmailMessage(BaseModel):
    id: str
    threadId: str
    labels: List[str]
    snippet: str
    subject: str = Field(default="")
    sender: str = Field(default="")
    sender_email: str = Field(default="")
    body: str
    date: str
    classification: Optional[str] = None
    summary: str = ""


# def extract_email(string: str) -> str:
#     return string.split('<')[1].split('>')[0]

def extract_email(address):
    """Extract email from a string that might be in the format 'Name <email@example.com>'"""
    match = re.search(r'<(.+@.+)>', address)
    if match:
        return match.group(1)
    return address if '@' in address else ''


def get_google_api_service(service_name: str, version: str):
    """
    Gets Google API service, which lets you log into Google APIs
    """
    SCOPES = ["https://mail.google.com/", "https://www.googleapis.com/auth/calendar"]
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


def decode_and_clean(encoded_data):
    decoded_data = base64.urlsafe_b64decode(encoded_data).decode('utf-8')
    soup = BeautifulSoup(decoded_data, 'html.parser')
    return soup.get_text(separator=' ', strip=True)


def get_message_body(payload):
    if payload.get('body', {}).get('data'):
        return decode_and_clean(payload['body']['data'])
    
    if payload.get('parts'):
        for part in payload['parts']:
            if part['mimeType'].startswith('text'):
                return decode_and_clean(part['body']['data'])
            elif part['mimeType'].startswith('multipart'):
                return get_message_body(part)
    
    return "No readable content found"



def get_messages_since_yesterday():
    service = get_google_api_service('gmail', 'v1')
    
    # Calculate yesterday's date and today's date
    yesterday = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    now = datetime.now()
    
    # Convert dates to RFC 3339 format
    yesterday_str = yesterday.strftime('%Y/%m/%d')
    now_str = now.strftime('%Y/%m/%d')
    
    # Construct the query
    query = f'after:{yesterday_str} before:{now_str}'
    
    # Get messages
    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])
    
    downloaded_messages = []
    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
        subject = next(header['value'] for header in msg['payload']['headers'] if header['name'].lower() == 'subject')
        sender = next(header['value'] for header in msg['payload']['headers'] if header['name'].lower() == 'from')
        sender_email = sender.split('<')[1].split('>')[0]
        sender = sender.split('<')[0].strip()
        
        body = get_message_body(msg['payload'])
        
        downloaded_messages.append(GmailMessage(
            id=msg['id'],
            threadId=msg['threadId'],
            labels=msg['labelIds'],
            snippet=msg['snippet'],
            subject=subject,
            sender=sender,
            sender_email=sender_email,
            body=body,
            date=msg['internalDate']
        ))
    
    return downloaded_messages


def get_attendee_email_threads(attendees: List[str], threads_per_attendee = 10):
    service = get_google_api_service('gmail', 'v1')
    
    # attendees = ['pranaviyer2@gmail.com', 'donny@apeiron.life']
    all_threads = []
    thread_attendee_map = defaultdict(set)
    for attendee in attendees:
        query = f"(to:{attendee} OR from:{attendee})"
        results = service.users().threads().list(userId='me', q=query, maxResults=threads_per_attendee).execute()
        threads = results.get('threads', [])
        all_threads.extend(threads)
        for thread in threads:
            thread_attendee_map[thread['id']].add(attendee)

    # get threads with multiple attendees
    multi_attendee_threads = []
    for thread in all_threads:
        if len(thread_attendee_map[thread['id']]) > 1:
            thread_data = service.users().threads().get(userId='me', id=thread['id']).execute()
            thread_msgs = []
            thread_participants = set()

            for msg in thread_data['messages']:
                headers = msg['payload']['headers']
                subject = next((header['value'] for header in headers if header['name'].lower() == 'subject'), 'No Subject')
                sender = next((header['value'] for header in headers if header['name'].lower() == 'from'), 'Unknown Sender')
                recipients = next((header['value'] for header in headers if header['name'].lower() == 'to'), '')
                cc = next((header['value'] for header in headers if header['name'].lower() == 'cc'), '')
                body = get_message_body(msg['payload'])
                
                sender_email = extract_email(sender)
                if recipients:
                    recipient_emails = [extract_email(r.strip()) for r in recipients.split(',')]
                else:
                    recipient_emails = []
                if cc:
                    recipient_emails += [extract_email(r.strip()) for r in cc.split(',')]
                thread_participants.update([sender_email] + recipient_emails)
                
                thread_msgs.append(GmailMessage(
                    id=msg['id'],
                    threadId=msg['threadId'],
                    labels=msg['labelIds'],
                    snippet=msg['snippet'],
                    subject=subject,
                    sender = sender.split('<')[0].strip(),
                    sender_email=sender_email,
                    body=body,
                    date=msg['internalDate']
                ))

            multi_attendee_threads.append({
                'messages': thread_msgs,
                'attendees': thread_attendee_map[thread['id']],
                'all_participants': thread_participants
            })

    # Sort threads by the number of attendees, in descending order
    multi_attendee_threads.sort(key=lambda x: len(x['attendees']), reverse=True)
    return multi_attendee_threads

    
if __name__ == '__main__':
    messages: List[GmailMessage] = get_messages_since_yesterday()
    print(f"Downloaded {len(messages)} messages.")
    for i, msg in enumerate(messages):
        print(f"\033[94mMessage {i+1}:\033[0m")
        print(f"Subject: {msg.subject}")
        print(f"From: {msg.sender}")
        print(f"Date: {msg.date}")
        print(f"Body: {msg.body[:200]}...")
        print("---")