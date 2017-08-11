import sys
import json
import logging

from .formatter import JsonFormatter


class StdoutFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno in (logging.DEBUG, logging.INFO)


class LogRecord(logging.LogRecord):
    def __init__(self, name, level, pathname, lineno,
                 msg, args, exc_info, func=None, sinfo=None, **kwargs):
        super(LogRecord, self).__init__(name, level, pathname, lineno, msg,
                                        args, exc_info, func, sinfo)
        self.extra = kwargs['extra']
        self.flatten = kwargs['flatten']


class JsonLogger(logging.Logger):
    def __init__(self, name='json_logger',
                 level=logging.DEBUG,
                 serializer=json.dumps,
                 stream=None,
                 flatten=False):
        """
        :type name: str
        :type level: int
        :type serializer: callable
        :param flatten: Same as passing flatten=True to all log method calls
        """
        super(JsonLogger, self).__init__(name, level)
        self.serializer = serializer
        self.flatten = flatten

        if stream:
            handler = self._make_handler(level=level, stream=stream)
            self.addHandler(handler)
        else:
            self.addHandler(self._stdout_handler)
            self.addHandler(self._stderr_handler)

    @property
    def _stdout_handler(self):
        """
        :rtype: logging.StreamHandler
        """
        handler = self._make_handler(level=logging.DEBUG, stream=sys.stdout)
        handler.addFilter(StdoutFilter())
        return handler

    @property
    def _stderr_handler(self):
        """
        :rtype: logging.StreamHandler
        """
        return self._make_handler(level=logging.WARNING, stream=sys.stderr)

    def _make_handler(self, level, stream):
        """
        :rtype: logging.StreamHandler
        """
        handler = logging.StreamHandler(stream)
        handler.setLevel(level)
        handler.setFormatter(JsonFormatter(self.serializer))

        return handler

    def makeRecord(self, name, level, fn, lno, msg, args, exc_info,
                   func=None, extra=None, sinfo=None):
        return LogRecord(name, level, fn, lno, msg, args, exc_info, func, sinfo,
                         extra=extra)

    def _log(self,
             level,
             msg,
             args,
             exc_info=None,
             extra=None,
             stack_info=False,
             flatten=False):
        """
        Low-level logging routine which creates a LogRecord and then calls
        all the handlers of this logger to handle the record.

        Overwritten to properly handle log methods kwargs
        """
        sinfo = None
        if logging._srcfile:
            #IronPython doesn't track Python frames, so findCaller raises an
            #exception on some versions of IronPython. We trap it here so that
            #IronPython can use logging.
            try:
                fn, lno, func, sinfo = self.findCaller(stack_info)
            except ValueError: # pragma: no cover
                fn, lno, func = "(unknown file)", 0, "(unknown function)"
        else: # pragma: no cover
            fn, lno, func = "(unknown file)", 0, "(unknown function)"
        if exc_info:
            if isinstance(exc_info, BaseException):
                exc_info = (type(exc_info), exc_info, exc_info.__traceback__)
            elif not isinstance(exc_info, tuple):
                exc_info = sys.exc_info()
        record = LogRecord(self.name, level, fn, lno, msg, args, exc_info,
                           func, sinfo, extra=extra, flatten=flatten or self.flatten)
        self.handle(record)
