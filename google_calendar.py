import os
from datetime import datetime, timezone

from google.auth import credentials
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib import flow
from googleapiclient.discovery import build

from cal import Calendar, Calendars, Event, Events


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

    events_collected = []

    while True:
        events = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=now,
                maxResults=10,
                singleEvents=True,
                orderBy="startTime",
                pageToken=page_token,
            )
            .execute()
        )
        found_events += len(events)
        event_tuples = []
        for event in events["items"]:
            if "dateTime" in event["start"]:
                start = datetime.fromisoformat(event["start"]["dateTime"]).astimezone(timezone.utc)
                end = datetime.fromisoformat(event["end"]["dateTime"]).astimezone(timezone.utc)
            else:
                start = datetime.fromisoformat(event["start"]["date"]).date()
                end = datetime.fromisoformat(event["end"]["date"]).date()
            if "description" in event:
                description = event["description"]
            else:
                description = None
            event_tuples.append(
                Event(
                    id=event["id"],
                    calendar_id=calendar_id,
                    start=start,
                    end=end,
                    name=event["summary"],
                    description=description,
                )
            )
            print(f"---- Event: {event['summary']} at {event['start']} ending {event['end']}")

        events_collected += event_tuples

        page_token = events.get("nextPageToken")
        if not page_token or found_events > 5:
            break

    return events_collected


if __name__ == "__main__":
    creds = authorize("secrets.json")
    service = build("calendar", "v3", credentials=creds)

    calendar_list = getCalendarList()

    vars = {
        "id": "id",
        "summary": "name",
        "description": "description",
        "timeZone": "time_zone",
        "selected": "active",
    }
    cals = []

    for calendar in calendar_list["items"]:
        found_vars = {}
        for var, name in vars.items():
            if var in calendar:
                found_vars[name] = calendar[var]
        if "summaryOverride" in calendar:
            found_vars["name"] = calendar["summaryOverride"]

        cals.append(Calendar(**found_vars))

    if len(cals) > 0:
        calendars = Calendars(cals)
        calendars.write()

    events_list = []

    for calendar_list_entry in calendar_list["items"]:
        print(f"Calendar: {calendar_list_entry['summary']}")

        events_list += getEvent(calendar_list_entry["id"])

    events = Events(events_list)
    events.write()
