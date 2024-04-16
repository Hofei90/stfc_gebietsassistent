import datetime
import pprint
import toml
import sched
import time
import utils
import subprocess
import sys

DATA = toml.load("data.toml")
REMIND_OFFSET = DATA["remind_offset"]
DEBUG = toml.load("config.toml")["debug"]


def create_text(territory, target_datetime):
    text = (f"**{DATA['ueberschrift']} {territory['system']} {target_datetime.strftime('am %d. %B')}**\n"
            f"{DATA['text'][0]} {territory['system']} {target_datetime.strftime('ist um %H:%M Uhr')}\n"
            f"{DATA['text'][1]} {toml.load('config.toml')['rule_link']}")
    return text


def send_reminder(scheduler, remind_offset, territory, target_datetime):
    text = create_text(territory, target_datetime)
    subprocess.run([sys.executable, "gebietsassistent_dc.py", text], check=False)
    pprint.pprint(create_territory_capture(scheduler, remind_offset, territory))


def create_territory_capture(scheduler, remind_offset, territory):
    target_ts = utils.get_target_ts(territory["date"], remind_time_offset=remind_offset)
    remind_ts = utils.get_remind_ts(target_ts, remind_offset)
    return scheduler.enterabs(remind_ts, 1, send_reminder,
                              (scheduler,
                               remind_offset,
                               territory,
                               datetime.datetime.fromtimestamp(target_ts)))


def create_territory_captures_after_start(scheduler, remind_offset, territories):
    reminders = []
    for territory in territories:
        if territory["priority"]:
            reminders.append(create_territory_capture(scheduler, remind_offset, territory))
    pprint.pprint(reminders)


def main():
    scheduler = sched.scheduler(time.time, time.sleep)
    create_territory_captures_after_start(scheduler,
                                          REMIND_OFFSET,
                                          toml.load("data.toml")["territories"])
    scheduler.run(blocking=True)


if __name__ == "__main__":
    main()
