import sys
import json
import logging

from .formatter import JsonFormatter


class StdoutFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno in (logging.DEBUG, logging.INFO)


class JsonLogger(logging.Logger):
    default_stream = sys.stdout
    error_stream = sys.stderr

    def __init__(self, name='json_logger',
                 level=logging.DEBUG,
                 serializer=json.dumps,
                 stream=None):
        """
        :type name: str
        :type level: int
        :type serializer: callable
        """
        super().__init__(name, level)
        self.serializer = serializer

        if stream:
            handler = self._make_handler(level=level, stream=stream)
            self.addHandler(handler)
        else:
            self.addHandler(self._stdout_handler)
            self.addHandler(self._stderr_handler)

    @property
    def _stdout_handler(self) -> 'logging.StreamHandler':
        handler = self._make_handler(level=logging.DEBUG, stream=sys.stdout)
        handler.addFilter(StdoutFilter())
        return handler

    @property
    def _stderr_handler(self) -> 'logging.StreamHandler':
        return self._make_handler(level=logging.WARNING, stream=sys.stderr)

    def _make_handler(self, level, stream) -> 'logging.StreamHandler':
        handler = logging.StreamHandler(stream)
        handler.setLevel(level)
        handler.setFormatter(JsonFormatter(self.serializer))

        return handler
