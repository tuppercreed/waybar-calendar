from datetime import datetime, date, time, timedelta
import sys, os, json, sqlite3

import pytz

from cal import Events, Event

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


def main():
    local_tz = pytz.timezone("Australia/Melbourne")
    tz_name = "Australia/Melbourne"
    start, end = find_time_bound(local_tz, custom_search=False)

    data = Events(window=(start, end))

    if len(data) == 1:
        event = data[0]
        info = {
            "start": event.local_start(tz_name).strftime("%H:%M"),
            "end": event.local_end(tz_name).strftime("%H:%M"),
            "title": event.name,
            "time_diff": int((event.start - start).total_seconds() / 60),
        }

        if info["time_diff"] > 60:
            hours = int(info["time_diff"] / 60)
            mins = int(info["time_diff"] - hours * 60)
            if mins > 0:
                mins_str = f" and {mins} minutes"
            else:
                mins_str = ""
            upcoming = f"{hours} hours{mins_str}"
        else:
            upcoming = f"{int(info['time_diff'])} minutes"

        d = {
            "text": f"Next event: {info['title']} starting in {upcoming}",
            "alt": "Alt-text",
            "tooltip": f"Start: {info['start']} \n End: {info['end']}",
        }

        sys.stdout.write(json.dumps(d))
        sys.stdout.write("\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
