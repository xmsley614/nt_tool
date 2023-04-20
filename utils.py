import datetime
import os
import time
from datetime import datetime, timedelta
from typing import List

import chime
import psutil


def date_range(start_date: str, end_date: str) -> List[str]:
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    date_list = []
    for n in range(int((end_dt - start_dt).days) + 1):
        d = start_dt + timedelta(n)
        date_list.append(d.strftime("%Y-%m-%d"))
    return date_list


def is_script_running(script_name):
    """a daemon program to check if python script is running

    :arg1: script name, "main.py"
    :returns: bool

    """
    for q in psutil.process_iter():
        if q.name().startswith("python"):
            if (len(q.cmdline()) > 1 and script_name in q.cmdline()[1]
                    and q.pid != os.getpid()):
                return True
    return False


def play_success_sound(num=3):
    chime.theme("zelda")
    for _ in range(num):
        chime.success()
        time.sleep(1)


def play_error_sound(num=3):
    chime.theme("zelda")
    for _ in range(num):
        chime.error()
        time.sleep(1)
