import functools
import logging
import os
import pprint
import sys
import traceback
from typing import Any, Callable, Literal, Optional, TypeAlias


LogLevel: TypeAlias = (
    Literal["debug"]
    | Literal["info"]
    | Literal["warning"]
    | Literal["error"]
    | Literal["critical"]
)


# ANSI codes that will generate colored text
def_color_map = {
    # reset should suffix any use of the other following prefixes
    "reset": "\x1b[0m",
    "brightred": "\x1b[31m",
    "red": "\x1b[31m",
    "green": "\x1b[32m",
    "yellow": "\x1b[33m",
    "blue": "\x1b[34m",
    "magenta": "\x1b[35m",
    "cyan": "\x1b[36m",
    "light_blue": "\x1b[94m",
    "darkgreen": "\x1b[92m",
    "purple": "\x1b[95m",
}

def_level_color = {
    "CRITICAL": "brightred",
    "ERROR": "red",
    "WARNING": "yellow",
    "INFO": "darkgreen",
    "DEBUG": None,
    "TRACE": None,
}

# We never truly want infinite output, 1000 lines is probably enough
config = {
    "DEBUG": {"max_lines": 1000},
    "INFO": {"max_lines": 10},
    "default": {"max_lines": 50},
}

formats = {
    "bare": "{msg}",
    "level": "{level_str}| {msg}",
    "name": "{level_str}| {name} | {msg}",
    "full": "{level_str}| {name} | {funcName}:{lineno} - {msg}",
}


# The default schema uses simpler logging for info-level logs, as these are
# intended for consumption at all times (non-debugging)
styles = {
    "default": {"INFO": "name", "DEBUG": "name", "default": "full"},
}


def color_text(text: str, color: Optional[str] = None) -> str:
    """Wraps text in a color code"""
    if not color:
        return text
    prefix = def_color_map.get(color, "")
    if not prefix:
        logging.warning(f"{color} not defined in color_map")
    suffix = def_color_map["reset"] if prefix else ""
    return f"{prefix}{text}{suffix}"


class FancyFormatter(logging.Formatter):
    """Adds colors and structure to a log output"""

    def __init__(self, style: dict[str, str]):
        # The schema will have level-dependent format strings
        self.style = style

        # Level colors can also be overridden by changing the dictionary at the top
        self.level_color = def_level_color

    def level_fmt(self, level: str) -> str:
        return color_text(f"{level: <8}", self.level_color.get(level))

    def format(self, record: logging.LogRecord) -> str:
        """Automatically called when logging a record"""
        # Allows modification of the record attributes
        record_dict = vars(record)

        # Prepare a pretty version of the message
        curr_conf = config.get(record.levelname, config["default"])
        pretty = record_dict["msg"]
        if isinstance(pretty, list | tuple | dict):
            pretty = pprint.pformat(pretty).strip("'\"")
        else:
            pretty = str(pretty)
        total_lines = pretty.count("\n")
        if total_lines > curr_conf["max_lines"]:
            lines = pretty.splitlines()
            # TODO Abstract away the lines left after truncation (e.g. the 2's and 4)
            trunc = total_lines - 6
            pretty = "\n".join(lines[:3] + [f"...truncated {trunc} lines"] + lines[-3:])
        record_dict["level_str"] = self.level_fmt(record.levelname)
        record_dict["msg"] = pretty

        # Shortcut characters for adding extra color
        if record_dict["msg"].startswith("#!"):
            record_dict["msg"] = color_text(record_dict["msg"][2:], "purple") + "\n"
        else:
            record_dict["msg"] += "\n"

        # First use an indicated format from the log message, otherwise use the level-based
        # format indicated in the style indicated during Logger initialization.
        formatter = formats[
            record_dict.get("fmt")
            or self.style.get(record.levelname, self.style["default"])
        ]

        return formatter.format(**record_dict)


def fancy_logger(name: str, style: dict[str, str] = styles["default"], level: int = 30):
    name_logger = logging.getLogger(name)
    name_logger.setLevel(level)
    name_logger.propagate = False

    # Make sure not to re-add the handlers if the same name is used
    if not name_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.terminator = ""
        handler.setFormatter(FancyFormatter(style=style))
        name_logger.addHandler(handler)

    return name_logger


def log_call(
    logger: Any, level: str = "info", ignore_idxs: set[int] = set()
) -> Callable[[Any], Any]:
    """Log the function and arguments."""

    def inner(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            display_args = tuple(
                [arg if idx not in ignore_idxs else "_" for idx, arg in enumerate(args)]
            )
            getattr(logger, level)(f"{func.__name__}{display_args}{kwargs}")
            result = func(*args, **kwargs)
            getattr(logger, level)(result)
            return result

        return wrapper

    return inner


def pretty_traceback(
    exc_name: str,
    exc_value: str,
    tb: list[traceback.FrameSummary],
) -> str:
    msg: list[str] = []
    for frame in tb:
        fileroot = os.path.splitext(os.path.basename(frame.filename))[0]
        loc = color_text(f"{fileroot:>9.9}:{frame.lineno:<3}", "blue")
        msg.append(f"  \u21B3 {loc} | {frame.line}")
    msg.append(color_text(f"    {exc_name}, {exc_value}", "red"))
    return "\n" + "\n".join(msg)


if __name__ == "__main__":
    log = fancy_logger("test")
    log.setLevel(10)
    for level in ["trace", "debug", "info", "warning", "error"]:
        getattr(log, level)(f"This is a {level} test")
    log.info("#!Purple message")
    log.info(
        {
            "title": "This is a pretty dictionary",
            "reasons": ["indentation", "length-checking"],
            "strings": [str(i) * 8 for i in range(20)],
            # "codes": [str(i) * 8 for i in range(50)],
        }
    )
