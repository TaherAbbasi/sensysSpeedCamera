import logging
import logging.handlers
from datetime import datetime
import inspect


class ClientLogger:
    def __init__(self, log_level=10):
        self.logger = logging.getLogger(__name__)
        # self.http_handler = logging.handlers.HTTPHandler(
        #     "{}:{}".format(dest_ip, dest_port),
        #     dest_url,
        #     method='GET',
        # )#.setFormatter(formatter)
        # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # self.http_handler.setFormatter(formatter)
        # self.logger.addHandler(self.http_handler)
        self.logger.setLevel(log_level)
        
    def info(self, message):
        previous_frame = inspect.currentframe().f_back
        (filename, line_number, function_name, lines, index) = inspect.getframeinfo(previous_frame)
        current_datetime = str(datetime.now())
        msg = "{ 'datetime':'%s', 'message':'%s', 'filename':'%s', 'line_number':'%s' ,'level_name':'info'}" % (current_datetime, message, filename, line_number)
        self.logger.info(msg)

    def debug(self, message):
        previous_frame = inspect.currentframe().f_back
        (filename, line_number, function_name, lines, index) = inspect.getframeinfo(previous_frame)
        current_datetime = str(datetime.now())
        msg = "{ 'datetime':'%s', 'message':'%s', 'filename':'%s', 'line_number':'%s' ,'level_name':'debug'}" % (current_datetime, message, filename, line_number)
        self.logger.debug(msg)
    def warning(self, message):
        previous_frame = inspect.currentframe().f_back
        (filename, line_number, function_name, lines, index) = inspect.getframeinfo(previous_frame)
        current_datetime = str(datetime.now())
        msg = "{ 'datetime':'%s', 'message':'%s', 'filename':'%s', 'line_number':'%s' ,'level_name':'warning'}" % (current_datetime, message, filename, line_number)
        self.logger.warning(msg)
    def error(self, message):
        previous_frame = inspect.currentframe().f_back
        (filename, line_number, function_name, lines, index) = inspect.getframeinfo(previous_frame)
        current_datetime = str(datetime.now())
        msg = "{ 'datetime':'%s', 'message':'%s', 'filename':'%s', 'line_number':'%s' ,'level_name':'error'}" % (current_datetime, message, filename, line_number)
        self.logger.error(msg)

    def critical(self, message):
        previous_frame = inspect.currentframe().f_back
        (filename, line_number, function_name, lines, index) = inspect.getframeinfo(previous_frame)
        current_datetime = str(datetime.now())
        msg = "{ 'datetime':'%s', 'message':'%s', 'filename':'%s', 'line_number':'%s' ,'level_name':'critical'}" % (current_datetime, message, filename, line_number)
        self.logger.critical(msg)
