import datetime
import pytz


def weekday_mapping(weekday):
    weekdays = {
        "Montag": 0,
        "Dienstag": 1,
        "Mittwoch": 2,
        "Donnerstag": 3,
        "Freitag": 4,
        "Samstag": 5,
        "Sonntag": 6,
    }
    return weekdays[weekday]


def get_target_datetime(date_string, current_datetime, remind_time_offset=0):
    weekday = date_string.split()[0]
    time_ = date_string.split()[1].split(":")
    target_datetime_utc = datetime.datetime.today().replace(hour=int(time_[0]), minute=int(time_[1]),
                                                            second=0, microsecond=0,
                                                            tzinfo=pytz.utc)
    target_datetime = target_datetime_utc.astimezone(pytz.timezone('Europe/Berlin'))
    weekdaynumber = weekday_mapping(weekday)
    one_day = datetime.timedelta(days=1)

    while True:
        if target_datetime.weekday() == weekdaynumber:
            if target_datetime > current_datetime + datetime.timedelta(minutes=remind_time_offset):
                break
            else:
                target_datetime = target_datetime + one_day
        else:
            target_datetime = target_datetime + one_day
    return target_datetime


def get_remaining_time(date_string):
    current_datetime_utc = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    current_datetime = current_datetime_utc.astimezone(pytz.timezone('Europe/Berlin'))
    target_datetime = get_target_datetime(date_string, current_datetime)
    remaining_time = target_datetime - current_datetime
    return int(remaining_time.total_seconds() * 1000)


def get_target_ts(date_string, remind_time_offset=0):
    current_datetime_utc = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    current_datetime = current_datetime_utc.astimezone(pytz.timezone('Europe/Berlin'))
    target_datetime = get_target_datetime(date_string, current_datetime, remind_time_offset)
    return target_datetime.timestamp()


def get_remind_ts(target_ts, remind_offset):
    return (datetime.datetime.fromtimestamp(target_ts) - datetime.timedelta(minutes=remind_offset)).timestamp()
