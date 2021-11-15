import os, sqlite3
from collections.abc import MutableSequence
import datetime
from sqlite3.dbapi2 import PARSE_DECLTYPES
from typing import NamedTuple, Optional

dir_path = os.path.dirname(os.path.realpath(__file__))
DB_PATH = f"{dir_path}/cal.db"


def cal_factory(cursor, row):
    return Calendar(*row)


def adapt_timezone(timezone):
    return repr(timezone)


def convert_timezone(timezone):
    return eval(timezone)


def convert_bool(boolean):
    return bool(boolean)


sqlite3.register_adapter(datetime.timezone, adapt_timezone)
sqlite3.register_converter("timezone", convert_timezone)
sqlite3.register_converter("bool", convert_bool)


class Calendar(NamedTuple):
    """Class for Calendar information.
    Attributes mirror the columns of sqlite3 table calendars"""

    id: str
    name: str

    description: Optional[str] = None
    time_zone: datetime.timezone = datetime.timezone.utc
    active: bool = False


class Calendars(MutableSequence):
    """A collection of Calendar objects with methods for sqlite3"""

    def __init__(self, calendars: list[Calendar] = None):
        super().__init__()

        if calendars is not None:
            self._calendars = calendars
        else:
            self._calendars = self._read()

    def __getitem__(self, i):
        return self._calendars[i]

    def __delitem__(self, i):
        del self._calendars[i]

    def __setitem__(self, i, new_value):
        self._calendars[i] = new_value

    def insert(self, i, new_value):
        self._calendars.insert(i, new_value)

    def __len__(self):
        return len(self._calendars)

    def __repr__(self):
        return f"Calendars([{', '.join([repr(cal) for cal in self._calendars])}])"

    def __str__(self):
        return f"[{', '.join([str(cal) for cal in self._calendars])}]"

    def write(self):
        """write all calendars to sqlite3 database"""
        con = sqlite3.connect(DB_PATH)
        con.execute(
            "CREATE TABLE IF NOT EXISTS calendars (id TEXT PRIMARY KEY NOT NULL, name TEXT, description TEXT, time_zone TEXT, active INTEGER, UNIQUE(id));"
        )

        with con:
            con.executemany(
                "INSERT OR REPLACE INTO calendars (id, name, description, time_zone, active) VALUES (?, ?, ?, ?, ?)",
                self._calendars,
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


if __name__ == "__main__":

    cal = Calendar(
        "1", "The first calendar", "Such a long description", datetime.timezone(datetime.timedelta(0), "A"), True
    )
    cal2 = Calendar("2", "Second cal")

    cals = Calendars([cal, cal2])

    cals.write()
