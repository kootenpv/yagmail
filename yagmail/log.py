"""
The logging options for yagmail. Note that the logger is set on the SMTP class.

The default is to only log errors. If wanted, it is possible to do logging with:

yag = SMTP()
yag.setLog(log_level = logging.DEBUG)

Furthermore, after creating a SMTP object, it is possible to overwrite and use your own logger by:

yag = SMTP()
yag.log = myOwnLogger
"""

import logging


def get_logger(log_level=logging.DEBUG, file_path_name=None):

    # create logger
    logger = logging.getLogger(__name__)

    logger.setLevel(logging.ERROR)

    # create console handler and set level to debug
    if file_path_name:
        ch = logging.FileHandler(file_path_name)
    elif log_level is None:
        logger.handlers = [logging.NullHandler()]
        return logger
    else:
        ch = logging.StreamHandler()

    ch.setLevel(log_level)

    # create formatter
    formatter = logging.Formatter(
        "%(asctime)s [yagmail] [%(levelname)s] : %(message)s", "%Y-%m-%d %H:%M:%S"
    )

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.handlers = [ch]

    return logger
