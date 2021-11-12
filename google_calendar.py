import os, sqlite3
from datetime import datetime, timezone

from google.auth import credentials
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib import flow
from googleapiclient.discovery import build


def authorize(cred_path, launch_browser=True):
    creds = None

    scopes = ["https://www.googleapis.com/auth/calendar.readonly"]

    # Previously stored flow credentials
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", scopes)

    # Seek new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            appflow = flow.InstalledAppFlow.from_client_secrets_file(
                client_secrets_file=cred_path,
                scopes=scopes,
            )
            if launch_browser:
                appflow.run_local_server()
            else:
                appflow.run_console()

            creds = appflow.credentials

            with open("token.json", "w") as token:
                token.write(creds.to_json())

    return creds


def getCalendarList():
    calendar_list = None
    page_token = None
    while True:
        calendar_list = service.calendarList().list(pageToken=page_token).execute()

        page_token = calendar_list.get("nextPageToken")
        if not page_token:
            break

    return calendar_list


def getEvent(calendar_id):
    page_token = None
    now = datetime.now(timezone.utc).isoformat()

    found_events = 0

    while True:
        events = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=now,
                maxResults=10,
                # singleEvents=True,
                # orderBy='startTime',
                pageToken=page_token,
            )
            .execute()
        )
        found_events += len(events)
        for event in events["items"]:
            print(f"---- Event: {event['summary']} at {event['start']} ending {event['end']}")
        page_token = events.get("nextPageToken")
        if not page_token or found_events > 5:
            break


def write_sql_calendars(calendars):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    path = f"{dir_path}/cal.db"
    con = sqlite3.connect(path)
    cur = con.cursor()

    cur.execute(
        "CREATE TABLE IF NOT EXISTS calendars (id TEXT PRIMARY KEY NOT NULL, summary TEXT, timeZone TEXT, active INTEGER, UNIQUE(id));"
    )
    cur.executemany("INSERT OR REPLACE INTO calendars (id, summary, timeZone) VALUES (?, ?, ?)", calendars)
    con.commit()


if __name__ == "__main__":
    creds = authorize("secrets.json")
    service = build("calendar", "v3", credentials=creds)

    calendar_list = getCalendarList()
    calendars = [(cal["id"], cal["summary"], cal["timeZone"]) for cal in calendar_list["items"]]

    write_sql_calendars(calendars)

    for calendar_list_entry in calendar_list["items"]:
        print(f"Calendar: {calendar_list_entry['summary']}")

        getEvent(calendar_list_entry["id"])
