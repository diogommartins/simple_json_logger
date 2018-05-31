import logging
try:
    from logging import _levelToName
except ImportError:  # pragma: no cover
    from logging import _levelNames as _levelToName

import traceback
from datetime import datetime
from inspect import istraceback


DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'

LOGGED_AT_FIELDNAME = 'logged_at'
LINE_NUMBER_FIELDNAME = 'line_number'
FUNCTION_NAME_FIELDNAME = 'function'
LOG_LEVEL_FIELDNAME = 'level'
MSG_FIELDNAME = 'msg'
FILE_PATH_FIELDNAME = 'file_path'


class JsonFormatter(logging.Formatter):
    level_to_name_mapping = _levelToName

    def __init__(self, serializer):
        super(JsonFormatter, self).__init__()
        self.serializer = serializer

    @staticmethod
    def _default_json_handler(obj):
        if isinstance(obj, datetime):
            return obj.strftime(DATETIME_FORMAT)
        elif istraceback(obj):
            tb = ''.join(traceback.format_tb(obj))
            return tb.strip().split('\n')
        elif isinstance(obj, Exception):
            return "Exception: %s" % str(obj)
        elif callable(obj):
            return obj()
        return str(obj)

    def format(self, record):
        msg = {
            LOGGED_AT_FIELDNAME: datetime.now().strftime(DATETIME_FORMAT),
            LINE_NUMBER_FIELDNAME: record.lineno,
            FUNCTION_NAME_FIELDNAME: record.funcName,
            LOG_LEVEL_FIELDNAME: self.level_to_name_mapping[record.levelno],
            FILE_PATH_FIELDNAME: record.pathname
        }
        if record.flatten:
            if isinstance(record.msg, dict):
                msg.update(record.msg)
            else:
                msg[MSG_FIELDNAME] = record.msg
        else:
            msg[MSG_FIELDNAME] = record.msg

        if record.extra:
            msg.update(record.extra)
        if record.exc_info:
            msg['exc_info'] = record.exc_info
        if record.exc_text:
            msg['exc_text'] = record.exc_text

        return self.serializer(msg,
                               default=self._default_json_handler,
                               **record.serializer_kwargs)
