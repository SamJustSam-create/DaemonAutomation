import os
import base64
import hashlib
import secrets
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
CREDENTIALS_FILE = Path("credentials/google_creds.json")
TOKEN_FILE = Path("credentials/token.json")
TIMEZONE = "Australia/Melbourne"
INVITEES = ["s.l.moloney@outlook.com", "moloneychris25954@gmail.com"]


def get_auth_url(redirect_uri: str) -> tuple[str, str, str]:
    """Return (auth_url, state, code_verifier) to redirect the user to Google OAuth."""
    flow = Flow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )
    code_verifier = secrets.token_urlsafe(96)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b"=").decode()
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        code_challenge=code_challenge,
        code_challenge_method="S256",
    )
    return auth_url, state, code_verifier


def exchange_code(code: str, state: str, redirect_uri: str, code_verifier: str) -> None:
    """Exchange OAuth code for credentials and save token."""
    flow = Flow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        scopes=SCOPES,
        state=state,
        redirect_uri=redirect_uri,
    )
    flow.fetch_token(code=code, code_verifier=code_verifier)
    creds = flow.credentials
    TOKEN_FILE.parent.mkdir(exist_ok=True)
    TOKEN_FILE.write_text(creds.to_json())


def _get_credentials() -> Credentials | None:
    if not TOKEN_FILE.exists():
        return None
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_FILE.write_text(creds.to_json())
    return creds if creds and creds.valid else None


def is_authenticated() -> bool:
    return _get_credentials() is not None


def create_event(shift: dict) -> dict:
    """Create a single Google Calendar event from a shift dict. Returns the created event."""
    creds = _get_credentials()
    if not creds:
        raise RuntimeError("Not authenticated with Google Calendar")

    service = build("calendar", "v3", credentials=creds)

    description = shift.get("description", "")
    if shift.get("special_uniform"):
        description += "\n\nSpecial Uniform is Required"

    event_body = {
        "summary": "Sam - Work",
        "description": description,
        "start": {
            "dateTime": shift["start"],
            "timeZone": TIMEZONE,
        },
        "end": {
            "dateTime": shift["end"],
            "timeZone": TIMEZONE,
        },
        "attendees": [{"email": e} for e in INVITEES],
        "reminders": {"useDefault": True},
    }

    created = service.events().insert(
        calendarId="primary",
        body=event_body,
        sendUpdates="all",
    ).execute()
    return created


def create_events(shifts: list[dict]) -> list[dict]:
    """Create multiple events. Returns list of results with success/error per shift."""
    results = []
    for shift in shifts:
        try:
            event = create_event(shift)
            results.append({
                "success": True,
                "date": shift["date"],
                "event_id": event.get("id"),
                "link": event.get("htmlLink"),
            })
        except Exception as e:
            results.append({
                "success": False,
                "date": shift["date"],
                "error": str(e),
            })
    return results
