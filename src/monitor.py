from utils import is_script_running, play_error_sound

if __name__ == "__main__":
    script_name = "auto_search.py"
    while True:
        if not is_script_running(script_name):
            print(f"{script_name} is not running!")
            play_error_sound()
