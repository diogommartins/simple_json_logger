import logging
import datetime
import traceback
from inspect import istraceback


class JsonFormatter(logging.Formatter):
    level_to_name_mapping = logging._levelToName

    def __init__(self, serializer):
        super(JsonFormatter, self).__init__()
        self.serializer = serializer

    @staticmethod
    def _default_json_handler(obj):
        if isinstance(obj, (datetime.date, datetime.time)):
            return obj.isoformat()
        elif istraceback(obj):
            tb = ''.join(traceback.format_tb(obj))
            return tb.strip()
        elif isinstance(obj, Exception):
            return "Exception: %s" % str(obj)
        return str(obj)

    def format(self, record):
        msg = {
            'logged_at': datetime.datetime.now().isoformat(),
            'line_number': record.lineno,
            'function': record.funcName,
            'level': self.level_to_name_mapping[record.levelno],
            'file_path': record.pathname
        }
        if record.flatten:
            if isinstance(record.msg, dict):
                msg.update(record.msg)
            else:
                msg['msg'] = record.msg
        else:
            msg['msg'] = record.msg

        if record.extra:
            msg.update(record.extra)
        if record.exc_info:
            msg['exc_info'] = record.exc_info
        if record.exc_text:
            msg['exc_text'] = record.exc_text

        return self.serializer(msg,
                               default=self._default_json_handler,
                               **record.serializer_kwargs)

