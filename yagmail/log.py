import logging

def getLogger(file_path_name = None, log_level = logging.DEBUG):

    # create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)

    # create console handler and set level to debug

    if file_path_name:
        ch = logging.FileHandler(file_path_name)
    else:
        ch = logging.StreamHandler()
        
    ch.setLevel(log_level)

    # create formatter
    formatter = logging.Formatter("%(asctime)s ; [yagmail] ; [%(levelname)s] ; %(message)s", "%Y-%m-%d %H:%M:%S")

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)
    
    return logger
