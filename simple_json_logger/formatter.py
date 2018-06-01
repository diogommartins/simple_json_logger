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
    default_fields = frozenset([
        LOG_LEVEL_FIELDNAME,
        LOGGED_AT_FIELDNAME,
        LINE_NUMBER_FIELDNAME,
        FUNCTION_NAME_FIELDNAME,
        FILE_PATH_FIELDNAME
    ])

    def __init__(self, serializer, exclude_fields=None):
        """
        :type serializer: Callable[[Dict], str]
        :type exclude_fields: Iterable[str]
        """
        super(JsonFormatter, self).__init__()
        self.serializer = serializer
        if exclude_fields is None:
            self.log_fields = self.default_fields
        else:
            self.log_fields = self.default_fields - set(exclude_fields)

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
    
    def formatter_fields_for_record(self, record):
        """
        :type record: LogRecord
        :rtype: Dict
        """
        default_fields = (
            (LOGGED_AT_FIELDNAME, datetime.now().strftime(DATETIME_FORMAT)),
            (LINE_NUMBER_FIELDNAME, record.lineno),
            (FUNCTION_NAME_FIELDNAME, record.funcName),
            (LOG_LEVEL_FIELDNAME, self.level_to_name_mapping[record.levelno]),
            (FILE_PATH_FIELDNAME, record.pathname)
        )

        for field, value in default_fields:
            if field in self.log_fields:
                yield field, value

    def format(self, record):
        msg = dict(self.formatter_fields_for_record(record))
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
