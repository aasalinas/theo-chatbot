import os
import base64
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText

# ✅ Gmail API Scopes (Read & Send Emails)
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send"]

# ✅ Authenticate & Get Gmail Service
def get_gmail_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)

# ✅ Fetch the Latest Emails
def get_latest_emails():
    service = get_gmail_service()
    results = service.users().messages().list(userId="me", maxResults=5).execute()
    messages = results.get("messages", [])

    emails = []
    for msg in messages:
        msg_data = service.users().messages().get(userId="me", id=msg["id"]).execute()
        headers = msg_data["payload"]["headers"]
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown Sender")
        snippet = msg_data.get("snippet", "No preview available.")

        emails.append(f"📩 **From:** {sender}\n📌 **Subject:** {subject}\n🔹 **Preview:** {snippet}\n")

    return "\n\n".join(emails) if emails else "No new emails."

# ✅ Send an Email
def send_email(to, subject, message_body):
    service = get_gmail_service()
    
    message = MIMEText(message_body)
    message["to"] = to
    message["subject"] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    message = {"raw": raw_message}
    sent_message = service.users().messages().send(userId="me", body=message).execute()
    return f"✅ Email sent to {to} with subject: {subject}"
