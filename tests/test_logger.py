import unittest
import logging
import json
import inspect
from datetime import datetime
from io import StringIO

from simple_json_logger import JsonLogger
from freezegun import freeze_time


class LoggerTests(unittest.TestCase):
    def setUp(self):
        self.buffer = StringIO()
        self.logger = JsonLogger(level=logging.DEBUG,
                                 stream=self.buffer)

    def test_it_logs_valid_json_string_if_message_is_json_serializeable(self):
        message = {
            'info': 'Se tem permissão, tamo dando sarrada',
            'msg': {
                'foo': 'bar',
                'baz': 'blu'
            }
        }

        self.logger.error(message)

        logged_content = self.buffer.getvalue()
        json_log = json.loads(logged_content)

        self.assertDictEqual(json_log['msg'], message)

    def test_it_logs_valid_json_string_if_message_isnt_json_serializeable(self):
        class FooJsonUnserializeable:
            pass

        obj = FooJsonUnserializeable()
        message = {'info': obj}
        self.logger.error(message)

        logged_content = self.buffer.getvalue()
        json_log = json.loads(logged_content)

        self.assertDictEqual(json_log['msg'], {'info': str(obj)})

    def test_it_escapes_strings(self):
        message = """"Aaaalgma coisa"paando `bem por'/\t \\" \" \' \n "aaa """

        self.logger.error(message)

        logged_content = self.buffer.getvalue()
        json_log = json.loads(logged_content)

        self.assertEqual(json_log['msg'], message)

    @freeze_time("2017-03-31 04:20:00")
    def test_it_logs_current_log_time(self):
        now = datetime.now().isoformat()

        self.logger.error("Batemos tambores, eles panela.")

        logged_content = self.buffer.getvalue()
        json_log = json.loads(logged_content)

        self.assertEqual(json_log['logged_at'], now)

    def test_it_logs_exceptions_tracebacks(self):
        exception_message = "Carros importados pra garantir os translados"

        try:
            raise Exception(exception_message)
        except Exception:
            self.logger.exception("Aqui nao é GTA, eh pior, eh Grajau")

        logged_content = self.buffer.getvalue()
        json_log = json.loads(logged_content)

        exc_class, exc_message, exc_traceback = json_log['exc_info']
        self.assertIn(member=exception_message,
                      container=exc_message)

        current_func_name = inspect.currentframe().f_code.co_name
        self.assertIn(member=current_func_name,
                      container=exc_traceback)

    def test_it_replaces_default_handlers_if_a_stream_is_provided(self):
        raise NotImplementedError