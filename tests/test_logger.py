import unittest
import logging
import json
import inspect
from datetime import datetime
from io import StringIO
try:
    from unittest.mock import Mock, call, patch
except ImportError:
    # python 2.7
    from mock import Mock, call, patch

from simple_json_logger import JsonLogger
from freezegun import freeze_time


class LoggerTests(unittest.TestCase):
    def setUp(self):
        self.buffer = StringIO()
        self.logger = JsonLogger(level=logging.DEBUG,
                                 stream=self.buffer)

    def test_it_logs_valid_json_string_if_message_is_json_serializeable(self):
        message = {
            'info': 'Se tem permissao, tamo dando sarrada',
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
            self.logger.exception("Aqui nao eh GTA, eh pior, eh Grajau")

        logged_content = self.buffer.getvalue()
        json_log = json.loads(logged_content)

        exc_class, exc_message, exc_traceback = json_log['exc_info']
        self.assertIn(member=exception_message,
                      container=exc_message)

        current_func_name = inspect.currentframe().f_code.co_name
        self.assertIn(member=current_func_name,
                      container=exc_traceback)

    def test_it_logs_datetime_objects(self):
        message = {
            'date': datetime.now().date(),
            'time': datetime.now().time(),
            'datetime': datetime.now()
        }

        self.logger.error(message)

        logged_content = self.buffer.getvalue()
        json_log = json.loads(logged_content)

        expected_output = {
            'date': message['date'].isoformat(),
            'time': message['time'].isoformat(),
            'datetime': message['datetime'].isoformat()
        }
        self.assertDictEqual(json_log['msg'], expected_output)

    def test_it_replaces_default_handlers_if_a_stream_is_provided(self):
        mocked_stream = Mock()
        mocked_logger = JsonLogger(stream=mocked_stream)

        info_msg = "Se o pensamento nasce livre, aqui ele nao eh nao"
        mocked_logger.info(info_msg)
        write_msg_call, write_line_break_call = mocked_stream.write.call_args_list
        self.assertEqual(write_line_break_call, call('\n'))
        self.assertIn(info_msg, write_msg_call[0][0])

        mocked_stream = Mock()
        mocked_logger = JsonLogger(stream=mocked_stream)

        mocked_logger.critical("BAR")
        write_msg_call, write_line_break_call = mocked_stream.write.call_args_list
        self.assertEqual(write_line_break_call, call('\n'))
        self.assertIn("BAR", write_msg_call[0][0])

    def test_it_calls_stdout_for_low_levels_and_stderr_for_high_levels(self):
        with patch("sys.stdout") as stdout:
            logger = JsonLogger()

            logger.debug("debug")
            logger.info("info")

            self.assertEqual(stdout.write.call_count, 4)

    def test_it_calls_stderr_for_high_log_leves(self):
        with patch("sys.stderr") as stderr:
            logger = JsonLogger()

            logger.warning("warning")
            logger.error("error")
            logger.critical("critical")

            self.assertEqual(stderr.write.call_count, 6)

    def test_extra_param_adds_content_to_document_root(self):
        with patch("sys.stdout") as stdout:
            logger = JsonLogger()

            extra = {
                'artist': "Joanne Shaw Taylor",
                'song': 'Wild is the wind'
            }
            logger.info("Music", extra=extra)

            self.assertEqual(stdout.write.call_count, 2)
            log_content = stdout.write.call_args_list[0][0][0]

            self.assertDictContainsSubset(extra, json.loads(log_content))
