from icalendar import Calendar, Event
from datetime import datetime, date, timedelta, time
from typing import Union
import pytz
import sqlite3


def read_sqlite_datetime(datetimebyte):
    return datetime.fromisoformat(datetimebyte.decode())


sqlite3.register_converter("datetime", read_sqlite_datetime)

con = sqlite3.connect("cal.db", detect_types=sqlite3.PARSE_COLNAMES)

cur = con.cursor()
cur.execute(
    "CREATE TABLE IF NOT EXISTS events (uid TEXT PRIMARY KEY NOT NULL, start TEXT, end TEXT, title TEXT, description TEXT, type TEXT, UNIQUE(uid));"
)
con.commit()

local_tz = pytz.timezone("Australia/Melbourne")
now_local_start = local_tz.localize(datetime(2021, 7, 14))
now_local_end = now_local_start + timedelta(1)
now_start = now_local_start.astimezone(pytz.utc)
now_end = now_local_end.astimezone(pytz.utc)


def datetime_to_date(obj: Union[datetime, date], end=False) -> date:
    if type(obj) is date:
        if not end:
            return pytz.utc.localize(datetime.combine(obj, datetime.min.time()))
        else:
            return pytz.utc.localize(datetime.combine(obj, datetime.min.time())) + timedelta(1)
    return obj


g = open("example.ics", "r")
gcal = Calendar.from_ical(g.read())
for cal in gcal.walk():
    for event in cal.subcomponents:
        if type(event) is not Event or "dtend" not in event:
            continue

        if type(event["dtstart"].dt) is date:
            event_type = "allday"
        else:
            event_type = "timed"
        start = datetime_to_date(event["dtstart"].dt)
        end = datetime_to_date(event["dtend"].dt, end=True)

        vars = (str(event["uid"]), start, end, str(event["summary"]), str(event["description"]), event_type)

        cur.execute("INSERT OR REPLACE INTO events VALUES (?, ?, ?, ?, ?, ?)", vars)

con.commit()

results = cur.execute(
    "SELECT start AS 'start [datetime]', end AS 'end [datetime]', title FROM events WHERE start BETWEEN ? AND ? AND type = 'timed'",
    (now_start, now_end),
)
matches = list(results)
print(matches)

con.close()

if __name__ == "__main__":
    print("main")
