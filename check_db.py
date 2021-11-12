import pytz
import sqlite3
from datetime import datetime, date, time, timedelta
import sys, os
import json

SEARCH_DATE = "2021-06-29"


def read_sqlite_datetime(datetimebyte):
    return datetime.fromisoformat(datetimebyte.decode())


sqlite3.register_converter("datetime", read_sqlite_datetime)


def find_time_bound(local_tz, custom_search=False):
    if custom_search:
        local_start = local_tz.localize(datetime.strptime(SEARCH_DATE, "%Y-%m-%d"))
    else:
        local_start = local_tz.localize(datetime.combine(datetime.now().date(), datetime.min.time()))
    start = local_start.astimezone(pytz.utc)
    end = start + timedelta(100)

    return start, end


def read(start, end):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    path = f"{dir_path}/cal.db"
    con = sqlite3.connect(path, detect_types=sqlite3.PARSE_COLNAMES)
    cur = con.cursor()

    results = cur.execute(
        "SELECT start AS 'start [datetime]', end AS 'end [datetime]', title, active FROM events INNER JOIN calendars ON events.calendar_id = calendars.id WHERE start BETWEEN ? AND ? AND type = 'timed' AND active = 1 ORDER BY start LIMIT 1",
        (start, end),
    )
    return list(results)


def main():
    local_tz = pytz.timezone("Australia/Melbourne")
    start, end = find_time_bound(local_tz, custom_search=False)
    data = read(start, end)

    if len(data) == 1:
        event_list = data[0]
        info = {
            "start": event_list[0].astimezone(local_tz).strftime("%Y-%m-%d"),
            "end": event_list[1].astimezone(local_tz).strftime("%Y-%m-%d"),
            "title": event_list[2],
            # "time_diff": int(
            #    (event_list[0] - local_tz.localize(datetime.now()).astimezone(pytz.utc)).total_seconds() / 60
            # ),
            "time_diff": int((event_list[0] - start).total_seconds() / 60),
        }

        if info["time_diff"] > 60:
            hours = int(info["time_diff"] / 60)
            mins = int(info["time_diff"] - hours * 60)
            upcoming = f"{hours} hours and {mins} minutes"
        else:
            upcoming = f"{int(info['time_diff'])} minutes"

        d = {
            "text": f"Next event: {info['title']} starting in {upcoming}",
            "alt": "Alt-text",
            "tooltip": "This is a toooltip",
        }

        sys.stdout.write(json.dumps(d))
        sys.stdout.write("\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
