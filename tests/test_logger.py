import unittest
import logging
import json
import inspect
from datetime import datetime
from io import StringIO
from unittest.mock import Mock, call, patch

from simple_json_logger import JsonLogger, formatter
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
        now = datetime.now().strftime(formatter.DATETIME_FORMAT)

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
        self.assertEqual(f'Exception: {exception_message}', exc_message)

        current_func_name = inspect.currentframe().f_code.co_name
        self.assertIn(current_func_name, exc_traceback[0])
        self.assertIn('raise Exception(exception_message)', exc_traceback[1])

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
            'datetime': message['datetime'].strftime(formatter.DATETIME_FORMAT)
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
        extra = {
            'artist': "Joanne Shaw Taylor",
            'song': 'Wild is the wind'
        }

        self.logger.info("Music", extra=extra)
        logged_content = json.loads(self.buffer.getvalue())

        self.assertDictContainsSubset(extra, logged_content)

    def test_flatten_param_adds_message_to_document_root(self):
        message = {
            'artist': 'Dave Meniketti',
            'song': 'Loan me a dime'
        }
        self.logger.info(message, flatten=True)
        logged_content = json.loads(self.buffer.getvalue())

        self.assertDictContainsSubset(message, logged_content)

    def test_flatten_method_parameter_overwrites_default_attributes(self):
        message = {'logged_at': 'Yesterday'}

        self.logger.info(message, flatten=True)
        logged_content = json.loads(self.buffer.getvalue())

        self.assertEqual(message['logged_at'], logged_content['logged_at'])

    def test_flatten_method_parameter_does_nothing_is_message_isnt_a_dict(self):
        message = "I'm not a dict :("

        self.logger.info(message, flatten=True)
        logged_content = json.loads(self.buffer.getvalue())

        self.assertEqual(message, logged_content['msg'])

    def test_flatten_instance_attr_adds_messages_to_document_root(self):
        self.logger.flatten = True

        message = {'The Jeff Healey Band': 'Cruel Little Number'}
        self.logger.info(message)
        logged_content = json.loads(self.buffer.getvalue())

        self.assertDictContainsSubset(message, logged_content)

    def test_flatten_instance_attr_overwrites_default_attributes(self):
        self.logger.flatten = True

        message = {'logged_at': 'Yesterday'}
        self.logger.info(message)
        logged_content = json.loads(self.buffer.getvalue())

        self.assertEqual(message['logged_at'], logged_content['logged_at'])

    @patch('logging.StreamHandler.terminator', '')
    def test_it_forwards_serializer_kwargs_parameter_to_serializer(self):
        message = {
            'logged_at': 'Yesterday',
            'line_number': 1,
            'function': 'print',
            'level': 'easy',
            'file_path': 'Somewhere over the rainbow'
        }
        options = {'indent': 2, 'sort_keys': True}
        self.logger.info(message, flatten=True, serializer_kwargs=options)

        logged_content = self.buffer.getvalue()
        expected_content = json.dumps(message, **options)

        self.assertEqual(logged_content, expected_content)

    @patch('logging.StreamHandler.terminator', '')
    def test_it_forwards_serializer_kwargs_instance_attr_to_serializer(self):
        self.logger.serializer_kwargs = {'indent': 2, 'sort_keys': True}

        message = {
            'logged_at': 'Yesterday',
            'line_number': 1,
            'function': 'print',
            'level': 'easy',
            'file_path': 'Somewhere over the rainbow'
        }
        self.logger.info(message, flatten=True)

        logged_content = self.buffer.getvalue()

        expected_content = json.dumps(message, **self.logger.serializer_kwargs)

        self.assertEqual(logged_content, expected_content)

    def test_extra_parameter_adds_content_to_root_of_all_messages(self):
        logger = JsonLogger(level=logging.DEBUG,
                            stream=self.buffer,
                            extra={'dog': 'Xablau'})
        message = {'log_message': 'Xena'}
        logger.info(message)

        logged_content = json.loads(self.buffer.getvalue())
        
        self.assertEqual(logged_content['msg']['log_message'], 'Xena')
        self.assertEqual(logged_content['dog'], 'Xablau')

    def test_extra_parameter_on_log_method_function_call_updates_extra_parameter_on_init(self):
        logger = JsonLogger(level=logging.DEBUG,
                            stream=self.buffer,
                            extra={'dog': 'Xablau'})
        message = {'log_message': 'Xena'}
        logger.info(message, extra={"ham": "eggs"})

        logged_content = json.loads(self.buffer.getvalue())

        self.assertEqual(logged_content['msg']['log_message'], 'Xena')
        self.assertEqual(logged_content['dog'], 'Xablau')
        self.assertEqual(logged_content['ham'], 'eggs')

    def test_callable_values_are_called_before_serialization(self):
        a_callable = Mock(return_value="I'm a callable that returns a string!")

        self.logger.info(a_callable)
        logged_content = json.loads(self.buffer.getvalue())
        self.assertEqual(logged_content['msg'], a_callable.return_value)
