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
from typing import Optional, Union


def get_logger(
    log_level: Optional[int] = logging.DEBUG,
    file_path_name: Optional[str] = None
) -> logging.Logger:

    # create logger
    logger = logging.getLogger(__name__)

    logger.setLevel(logging.ERROR)

    ch: Union[logging.FileHandler, logging.StreamHandler, None] = None

    # create console handler and set level to debug
    if file_path_name:
        ch = logging.FileHandler(file_path_name)
    elif log_level is None:
        logger.handlers = [logging.NullHandler()]
        return logger
    else:
        ch = logging.StreamHandler()

    if ch is not None and log_level is not None:
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
