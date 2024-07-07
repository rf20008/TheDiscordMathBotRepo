import datetime
import time
import traceback

MONTH_NAMES = {
    1: "January",
    2: "February,",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}


async def log_error(error, file_path="", send_to_webhook=False):
    log_error_to_file(error, file_path)
    if send_to_webhook:
        raise NotImplementedError("Not done yet")


def log_error_to_file(error, file_path=""):
    "Log the error to a file"
    if not isinstance(file_path, str):
        raise TypeError("file_path is not a string")
    if not isinstance(error, BaseException):
        raise TypeError("error is not an error")
    if file_path == "":
        now = datetime.datetime.now()
        file_path = (
            "error_logs/"
            + str(now.year)
            + " "
            + str(MONTH_NAMES[now.month])
            + " "
            + str(now.day)
            + ".txt"
        )
    err_msg = traceback.format_exception(type(error), error, tb=error.__traceback__)
    msg = time.asctime() + "\n\n" + "".join([str(item) for item in err_msg]) + "\n\n"

    try:
        with open(file_path, "a") as f:
            f.write(msg)
    except Exception as exc:
        raise Exception(
            "***File path not found.... or maybe something else happened.... anyway please report this :)***"
        ) from exc
