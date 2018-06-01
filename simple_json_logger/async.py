import asyncio
import json
import logging
import sys
from asyncio.streams import StreamWriter
from asyncio.unix_events import _set_nonblocking
from io import TextIOBase
from typing import Type

from simple_json_logger.logger import BaseJsonLogger, StdoutFilter


class StdoutProtocol(asyncio.Protocol):
    pass


class StderrProtocol(asyncio.Protocol):
    pass


class AsyncStreamHandler(logging.StreamHandler):
    async def handle(self, record):
        """
        Conditionally emit the specified logging record.
        Emission depends on filters which may have been added to the handler.
        """
        rv = self.filter(record)
        if rv:
            await self.emit(record)
        return rv

    async def emit(self, record):
        try:
            msg = self.format(record) + self.terminator

            await self.stream.write(msg.encode())
            await self.stream.drain()
        except Exception:
            return  # fixme: Do something on error
            self.handleError(record)


class AsyncJsonLogger(BaseJsonLogger):
    def __init__(self, *,
                 loop=None,
                 stdout_writer: StreamWriter,
                 stderr_writer: StreamWriter,
                 name='json_logger',
                 level=logging.DEBUG,
                 serializer=json.dumps,
                 flatten=False,
                 serializer_kwargs=None,
                 extra=None):

        super().__init__(name, level, serializer, flatten, serializer_kwargs,
                         extra)
        self.loop = loop
        self.stdout_writer = stdout_writer
        self.stderr_writer = stderr_writer

        self.addHandler(self.__stdout_handler)
        self.addHandler(self.__stderr_handler)

    @property
    def __stdout_handler(self):
        """
        :rtype: logging.StreamHandler
        """
        handler = self._make_handler(level=logging.DEBUG,
                                     stream=self.stdout_writer,
                                     handler_cls=AsyncStreamHandler)
        handler.addFilter(StdoutFilter())
        return handler

    @property
    def __stderr_handler(self):
        """
        :rtype: logging.StreamHandler
        """
        return self._make_handler(level=logging.WARNING,
                                  stream=self.stderr_writer,
                                  handler_cls=AsyncStreamHandler)

    @classmethod
    async def make_stream_writer(cls,
                                 protocol_factory: Type[asyncio.Protocol],
                                 pipe: TextIOBase,
                                 loop) -> StreamWriter:
        loop = loop or asyncio.get_event_loop()

        _set_nonblocking(pipe.fileno())
        transport, protocol = await loop.connect_write_pipe(protocol_factory,
                                                            pipe)
        return StreamWriter(transport=transport,
                            protocol=protocol,
                            reader=None,
                            loop=loop)

    @classmethod
    async def init_async(cls, *,
                         loop=None,
                         name='json_logger',
                         level=logging.DEBUG,
                         serializer=json.dumps,
                         flatten=False,
                         serializer_kwargs=None,
                         extra=None):
        loop = loop or asyncio.get_event_loop()

        stdout_writer = await cls.make_stream_writer(
            protocol_factory=StdoutProtocol,
            pipe=sys.stdout,
            loop=loop
        )

        stderr_writer = await cls.make_stream_writer(
            protocol_factory=StderrProtocol,
            pipe=sys.stderr,
            loop=loop
        )

        return cls(
            loop=loop,
            stdout_writer=stdout_writer,
            stderr_writer=stderr_writer,
            name=name,
            level=level,
            serializer=serializer,
            flatten=flatten,
            serializer_kwargs=serializer_kwargs,
            extra=extra
        )

    async def callHandlers(self, record):
        """
        Pass a record to all relevant handlers.

        Loop through all handlers for this logger and its parents in the
        logger hierarchy. If no handler was found, raises an error. Stop
        searching up the hierarchy whenever a logger with the "propagate"
        attribute set to zero is found - that will be the last logger
        whose handlers are called.
        """
        c = self
        found = 0
        while c:
            for handler in c.handlers:
                found = found + 1
                if record.levelno >= handler.level:
                    await handler.handle(record)
            if not c.propagate:
                c = None  # break out
            else:
                c = c.parent
        if found == 0:
            raise Exception("No handlers could be found for logger")

    async def handle(self, record):
        """
        Call the handlers for the specified record.

        This method is used for unpickled records received from a socket, as
        well as those created locally. Logger-level filtering is applied.
        """
        if (not self.disabled) and self.filter(record):
            await self.callHandlers(record)

    async def _log(self,
                   level,
                   msg,
                   args,
                   exc_info=None,
                   extra=None,
                   stack_info=False,
                   flatten=False,
                   serializer_kwargs={}):
        record = self.make_log_record(level, msg, args, exc_info, extra,
                                      stack_info, flatten, serializer_kwargs)
        await self.handle(record)

    async def info(self, msg, *args, **kwargs):
        if self.isEnabledFor(logging.INFO):
            await self._log(logging.INFO, msg, args, **kwargs)

    async def error(self, msg, *args, **kwargs):
        if self.isEnabledFor(logging.ERROR):
            await self._log(logging.ERROR, msg, args, **kwargs)
