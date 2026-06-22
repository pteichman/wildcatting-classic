import logging
from logging.handlers import RotatingFileHandler


def startLogger(filename: str) -> None:
    root = logging.getLogger()

    # This specifies the deepest possible log level, so our handlers
    # get a chance at all messages.  The levels of things that are
    # actually logged are below, on the handlers.
    root.setLevel(logging.DEBUG)

    # Start with a clean slate, in case something has started the log system
    for h in root.handlers:
        root.removeHandler(h)

    format = "%(asctime)s [%(levelname)s] %(message)s"

    fileHandler = RotatingFileHandler(
        filename, maxBytes=10 * 1024 * 1024, backupCount=3
    )
    fileHandler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(format, "%Y-%m-%d %T")
    fileHandler.setFormatter(formatter)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(logging.ERROR)
    formatter = logging.Formatter(format, "%T")
    consoleHandler.setFormatter(formatter)

    root.addHandler(fileHandler)
    root.addHandler(consoleHandler)
