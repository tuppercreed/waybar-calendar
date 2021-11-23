import os, sqlite3
from collections.abc import MutableMapping
from collections import defaultdict
from datetime import datetime, date
import pytz
from typing import NamedTuple, Optional, Union

dir_path = os.path.dirname(os.path.realpath(__file__))
DB_PATH = f"{dir_path}/cal.db"


def cal_factory(cursor, row):
    return Calendar(*row)


def convert_bool(boolean):
    return bool(int(boolean))


def convert_datetime(datetimebyte):
    string = datetimebyte.decode()
    datetime_obj = datetime.fromisoformat(string)
    if len(string) == 10:
        return datetime_obj.date()
    else:
        return datetime_obj


def adapt_datetime(datetime_obj):
    return datetime_obj.isoformat()


sqlite3.register_converter("datetime", convert_datetime)
sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_adapter(date, adapt_datetime)
sqlite3.register_converter("bool", convert_bool)


class Event(NamedTuple):
    """Class for Event information.
    Attributes mirror the columns of sqlite3 table events"""

    id: str
    calendar_id: str
    start: Union[datetime, date]
    end: Union[datetime, date]
    name: str

    description: Optional[str] = None

    def localize(self, obj: Union[datetime, date], tz_name):
        if type(obj) is datetime:
            tz = pytz.timezone(tz_name)
            return obj.astimezone(tz)
        else:
            return obj

    def local_start(self, tz_name):
        return self.localize(self.start, tz_name)

    def local_end(self, tz_name):
        return self.localize(self.end, tz_name)


CALENDAR_DOWNLOADED_INFO = ("name", "description", "time_zone")
CALENDAR_PROGRAM_INFO = ("id", "active")


class Calendar(NamedTuple):
    """Class for Calendar information.
    Attributes mirror the columns of sqlite3 table calendars"""

    # Downloaded Information
    id: str
    name: str
    description: Optional[str] = None
    time_zone: str = pytz.utc.zone

    # Program Information
    active: bool = False
    # events: list[Event] = []


class GroupedObject(MutableMapping):
    """A collection of objects intended to be inherited by Calendars and Events"""

    def __init__(self, *args, **kwargs):
        """Use the object dict"""
        self.__dict__.update(*args, **kwargs)

    def __getitem__(self, key):
        return self.__dict__[key]

    def __delitem__(self, key):
        del self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __repr__(self):
        return "{}, GroupedObject({})".format(super(GroupedObject, self).__repr__(), self.__dict__)

    def __str__(self):
        return f"[{', '.join([str(cal) for cal in self.__dict__])}]"


class Calendars(GroupedObject):
    """A collection of Calendar objects with methods for sqlite3"""

    def __init__(self, calendars: dict[str, Calendar] = None):
        read_calendars = self._read()
        if calendars is not None:
            calendars = self.resolve_calendars(read_calendars, calendars)
        else:
            calendars = read_calendars

        super().__init__(**calendars)

    def __repr__(self):
        return f"Calendars([{', '.join([repr(cal) for cal in self.__dict__])}])"

    def resolve_calendars(self, c1: dict[str, Calendar], c2: dict[str, Calendar]):
        """Overrides downloaded information in c1 with any information in c2 and returns completed c1"""
        for id, calendar in c2.items():
            if id in c1:
                attrs = {}
                for elem in CALENDAR_DOWNLOADED_INFO:
                    attrs[elem] = getattr(calendar, elem)
                for elem in CALENDAR_PROGRAM_INFO:
                    attrs[elem] = getattr(c1[id], elem)
                c1[id] = Calendar(**attrs)
            c1[id] = calendar

        return c1

    def active(self):
        return {key: value for key, value in self.__dict__.items() if value.active}

    def write(self):
        """write all calendars to sqlite3 database"""
        con = sqlite3.connect(DB_PATH)
        con.execute(
            "CREATE TABLE IF NOT EXISTS calendars (id TEXT PRIMARY KEY NOT NULL, name TEXT, description TEXT, time_zone TEXT, active INTEGER, UNIQUE(id));"
        )

        with con:
            con.executemany(
                "INSERT OR REPLACE INTO calendars (id, name, description, time_zone, active) VALUES (?, ?, ?, ?, ?)",
                self.__dict__.values(),
            )

    def _read(self):
        """read all calendars from sqlite3 database"""
        con = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_COLNAMES)

        # Each row of the calendars table is constructed as a Calendar object through cal_factory
        con.row_factory = cal_factory

        with con:
            results = list(
                con.execute(
                    "SELECT id, name, description, time_zone AS 'time_zone [timezone]', active AS 'active [bool]' FROM calendars;"
                )
            )

        results_dict = {cal.id: cal for cal in results}

        return results_dict

    def _pool_events(self, events):
        cal_ids = {cal.id: i for i, cal in enumerate(self._calendars)}

        for event in events:
            self.__dict__[cal_ids[event.cal_id]].events.append(event)


class Events(GroupedObject):
    """A collection of Event objects with methods for sqlite3"""

    def __init__(
        self, events: dict[str, Event] = None, window: Union[tuple[datetime, datetime], None] = None, limit: int = 0
    ):
        if events is None:
            events = self._read(window, limit)
        super().__init__(**events)

    def __repr__(self):
        return f"Events([{', '.join([repr(cal) for cal in self.__dict__])}])"

    def _read(self, window: Union[tuple[datetime, datetime], None] = None, limit: int = 0):
        con = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_COLNAMES)

        con.row_factory = lambda x, y: Event(*y)

        vars = ["id", "calendar_id", "start AS 'start [datetime]'", "end AS 'end [datetime]'"]
        if window is None:
            vars += ["name", "description"]

            join = ""
            where = ""
        else:
            vars.pop(0)
            vars.insert(0, "events.id")
            vars += ["events.name", "events.description"]

            join = "INNER JOIN calendars ON events.calendar_id = calendars.id"
            where = "WHERE start BETWEEN ? and ? AND active = 1"

        order_by = "ORDER BY start"

        if not limit:
            limit_str = ""
        else:
            limit_str = f"LIMIT {limit}"

        query = f"""SELECT 
        {", ".join(vars)}
        FROM events
        {join}
        {where}
        {order_by}
        {limit_str}
        """

        with con:
            if window is None:
                results = list(con.execute(query))
            else:
                results = list(con.execute(query, (window[0], window[1])))

        results_dict = {event.id: event for event in results}

        return results_dict

    def write(self):
        """write all events to sqlite3 database"""
        con = sqlite3.connect(DB_PATH)
        con.execute(
            "CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY NOT NULL, calendar_id TEXT, start TEXT, end TEXT, name TEXT, description TEXT, UNIQUE(id));"
        )

        with con:
            con.executemany(
                "INSERT OR REPLACE INTO events (id, calendar_id, start, end, name, description) VALUES (?, ?, ?, ?, ?, ?)",
                self.__dict__.values(),
            )

    def group(self, TZ_NAME, interval: Union[str, None] = None):
        """Takes a str interval as a strftime format code
        Returns a dictionary of lists of Event, split by the result of the format code"""
        if interval is None:
            interval = "%Y-%m-%d"
        split = defaultdict(list)
        for event in self.__dict__.values():
            split[event.local_start(TZ_NAME).strftime(interval)].append(event)

        return split


if __name__ == "__main__":

    events = Events()

    events.group()

    cals = Calendars()

    # cals.read_events()

    cal = Calendar("1", "The first calendar", "Such a long description", "US/Eastern", True)
    cal2 = Calendar("2", "Second cal")

    cals = Calendars({"1": cal, "2": cal2})

    cals.write()
