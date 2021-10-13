from datetime import datetime
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from pythonjsonlogger import jsonlogger

def create_logger():
    path = Path.home().joinpath('invader_vim.log')

    logger = logging.getLogger('invader_vim')
    # logger.setLevel(logging.INFO)
    logger.setLevel(logging.DEBUG)

    handler = TimedRotatingFileHandler(path, when='h', interval=1, backupCount=5)
    formatter = JsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


class JsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(JsonFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get('timestamp'):
            now = datetime.fromtimestamp(record.created).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            log_record['timestamp'] = now
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname


