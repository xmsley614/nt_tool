import os

from utils import is_script_running


def kill_proc(script_name):
    if is_script_running(script_name):
        cmd = f"ps aux | grep {script_name}" + " | awk {'print $2'} | xargs kill -9"
        os.system(cmd)


def main():
    kill_proc("auto_search.py")
    kill_proc("monitor.py")

    cmd = "nohup python auto_search.py > search.log &"
    os.system(cmd)
    cmd = "python monitor.py &"
    os.system(cmd)


if __name__ == "__main__":
    main()
