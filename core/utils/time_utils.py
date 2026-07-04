from datetime import datetime
import pytz

from config import TIMEZONE


IST = pytz.timezone(TIMEZONE)


def now_ist():
    return datetime.now(IST)


def to_ist(dt):
    if dt.tzinfo is None:
        return IST.localize(dt)

    return dt.astimezone(IST)


def get_today():
    return now_ist().date()


def format_date(dt):
    return dt.strftime("%Y-%m-%d")


def format_time(dt):
    return dt.strftime("%H:%M:%S")


def format_day(dt):
    return dt.strftime("%A")