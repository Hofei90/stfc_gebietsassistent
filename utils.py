import datetime

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

def get_target_datetime(date_string, current_datetime=None, remind_time_offset=0):
    weekday_str, time_str = date_string.split()
    hour, minute = map(int, time_str.split(":"))
    target_weekday = weekday_mapping(weekday_str)

    if current_datetime is None:
        current_datetime = datetime.datetime.now(datetime.timezone.utc)

    target = current_datetime.replace(hour=hour, minute=minute, second=0, microsecond=0)

    one_day = datetime.timedelta(days=1)
    while True:
        if target.weekday() == target_weekday:
            if target > current_datetime + datetime.timedelta(minutes=remind_time_offset):
                break
        target += one_day

    return target

def get_remaining_time(date_string):
    now = datetime.datetime.now(datetime.timezone.utc)
    target = get_target_datetime(date_string, now)
    delta = target - now
    return int(delta.total_seconds() * 1000)

def get_target_ts(date_string, remind_time_offset=0):
    dt = get_target_datetime(date_string, remind_time_offset=remind_time_offset)
    return dt.timestamp()

def get_remind_ts(target_ts, remind_offset):
    return (datetime.datetime.fromtimestamp(target_ts, tz=datetime.timezone.utc) -
            datetime.timedelta(minutes=remind_offset)).timestamp()
