import pytz
import sqlite3
from datetime import datetime, date, time, timedelta
import sys, os
import json


def read_sqlite_datetime(datetimebyte):
    return datetime.fromisoformat(datetimebyte.decode())


sqlite3.register_converter("datetime", read_sqlite_datetime)


def find_time_bound(local_tz):
    """now_local_start = local_tz.localize(datetime(2021, 7, 14))
    now_local_end = now_local_start + timedelta(1)
    now_start = now_local_start.astimezone(pytz.utc)
    now_end = now_local_end.astimezone(pytz.utc)

    return now_start, now_end"""
    start = datetime.combine(datetime.now().date(), datetime.min.time()) - timedelta(200)
    end = start + timedelta(50)

    return start, end


def read(start, end):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    path = f"{dir_path}/cal.db"
    con = sqlite3.connect(path, detect_types=sqlite3.PARSE_COLNAMES)
    cur = con.cursor()

    results = cur.execute(
        "SELECT start AS 'start [datetime]', end AS 'end [datetime]', title FROM events WHERE start BETWEEN ? AND ? AND type = 'timed' ORDER BY start LIMIT 1",
        (start, end),
    )
    return list(results)


def main():

    local_tz = pytz.timezone("Australia/Melbourne")
    start, end = find_time_bound(local_tz)
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
            "time_diff": int((event_list[0] - local_tz.localize(start)).total_seconds() / 60),
        }

        d = {
            "text": f"Next event: {info['title']} starting in {info['time_diff']} minutes",
            "alt": "Alt-text",
            "tooltip": "This is a toooltip",
        }

        sys.stdout.write(json.dumps(d))
        sys.stdout.write("\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
