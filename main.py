import bot
import sys
import datetime
import logging

def get_loglevel(level_str):
    # there has to be a better way to do this but I don't know it
    if level_str == "critical":
        return logging.CRITICAL
    elif level_str == "error":
        return logging.ERROR
    elif level_str == "warning":
        return logging.WARNING
    elif level_str == "info":
        return logging.INFO
    elif level_str == "debug":
        return logging.DEBUG

if __name__ == "__main__":
    if len(sys.argv) == 3:
        date = str(datetime.datetime.now(datetime.timezone.utc)).replace(":", " ")
        fname = f"logs/LOG_{date}.txt"
        file_loglevel = sys.argv[2].lower().strip()
        if file_loglevel not in ("critical", "error", "warning", "info", "debug"):
            print("Unknown logging level.")
            sys.exit()
        file_loglevel = get_loglevel(file_loglevel)
        file_handler = logging.FileHandler(filename=fname, encoding="utf-8", mode="w")
        file_handler.setLevel(file_loglevel)
    else:
        file_handler = None

    if len(sys.argv) == 2:
        cmd_loglevel = sys.argv[1].lower().strip()
        if cmd_loglevel not in ("critical", "error", "warning", "info", "debug"):
            print("Unknown logging level.")
            sys.exit()
        cmd_loglevel = get_loglevel(cmd_loglevel)
    else:
        cmd_loglevel = logging.INFO

    bot.run_bot(file_handler, cmd_loglevel)
