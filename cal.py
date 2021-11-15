import os, sqlite3
from collections.abc import MutableSequence
from datetime import datetime, date
import pytz
from sqlite3.dbapi2 import PARSE_DECLTYPES
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


class Calendar(NamedTuple):
    """Class for Calendar information.
    Attributes mirror the columns of sqlite3 table calendars"""

    id: str
    name: str

    description: Optional[str] = None
    time_zone: str = pytz.utc.zone
    active: bool = False
    # events: list[Event] = []


class GroupedObject(MutableSequence):
    """A collection of objects intended to be inherited by Calendars and Events"""

    def __init__(self, obj: list[Union[NamedTuple, Event, Calendar]] = None):
        self.group = obj
        super().__init__()

    def __getitem__(self, i):
        return self.group[i]

    def __delitem__(self, i):
        del self.group[i]

    def __setitem__(self, i, new_value):
        self.group[i] = new_value

    def insert(self, i, new_value):
        self.group.insert(i, new_value)

    def __len__(self):
        return len(self.group)

    def __repr__(self):
        return f"GroupedObject([{', '.join([repr(cal) for cal in self.group])}])"

    def __str__(self):
        return f"[{', '.join([str(cal) for cal in self.group])}]"


class Calendars(GroupedObject):
    """A collection of Calendar objects with methods for sqlite3"""

    def __init__(self, calendars: list[Calendar] = None):
        if calendars is None:
            calendars = self._read()

        super().__init__(obj=calendars)

    def __repr__(self):
        return f"Calendars([{', '.join([repr(cal) for cal in self.group])}])"

    def write(self):
        """write all calendars to sqlite3 database"""
        con = sqlite3.connect(DB_PATH)
        con.execute(
            "CREATE TABLE IF NOT EXISTS calendars (id TEXT PRIMARY KEY NOT NULL, name TEXT, description TEXT, time_zone TEXT, active INTEGER, UNIQUE(id));"
        )

        with con:
            con.executemany(
                "INSERT OR REPLACE INTO calendars (id, name, description, time_zone, active) VALUES (?, ?, ?, ?, ?)",
                self.group,
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

        return results

    def _pool_events(self, events):
        cal_ids = {cal.id: i for i, cal in enumerate(self._calendars)}

        for event in events:
            self.group[cal_ids[event.cal_id]].events.append(event)


class Events(GroupedObject):
    def __init__(self, events: list[Event] = None):
        if events is None:
            events = self._read()
        super().__init__(obj=events)

    def __repr__(self):
        return f"Events([{', '.join([repr(cal) for cal in self.group])}])"

    def _read(self):
        con = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_COLNAMES)

        con.row_factory = lambda x, y: Event(*y)

        with con:
            results = list(
                con.execute(
                    "SELECT id, calendar_id, start AS 'start [datetime]', end AS 'end [datetime]', name, description FROM events;"
                )
            )

        return results

    def write(self):
        """write all events to sqlite3 database"""
        con = sqlite3.connect(DB_PATH)
        con.execute(
            "CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY NOT NULL, calendar_id TEXT, start TEXT, end TEXT, name TEXT, description TEXT, UNIQUE(id));"
        )

        with con:
            con.executemany(
                "INSERT OR REPLACE INTO events (id, calendar_id, start, end, name, description) VALUES (?, ?, ?, ?, ?, ?)",
                self.group,
            )


if __name__ == "__main__":

    events = Events()

    cals = Calendars()

    # cals.read_events()

    cal = Calendar("1", "The first calendar", "Such a long description", "US/Eastern", True)
    cal2 = Calendar("2", "Second cal")

    cals = Calendars([cal, cal2])

    cals.write()
