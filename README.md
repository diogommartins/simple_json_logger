[TOC]

# Simple Json Logger
[![Build Status](https://travis-ci.org/diogommartins/simple_json_logger.svg?branch=master)](https://travis-ci.org/diogommartins/simple_json_logger)
[![codecov](https://codecov.io/gh/diogommartins/simple_json_logger/branch/master/graph/badge.svg)](https://codecov.io/gh/diogommartins/simple_json_logger)

A simple, thin layer, drop-in replacement of python built-in Logger from
the `logging` module, that grants to always log valid json output.

## Installation

`pip install simple_json_logger`

## Testing

`python -m unittest discover`

## Usage

### Hello world

``` python

from simple_json_logger import JsonLogger


def foo():
    logger = JsonLogger()

    logger.info("Hello world!")

foo()
>>> {"msg": "Hello world!", "logged_at": "2017-03-31T02:10:16.786569", "line_number": 6, "function": "foo", "level": "INFO", "file_path": "/Volumes/partition2/Users/diogo/PycharmProjects/simple_json_logger/bla.py"}
```


### stdin / stderr

By default, JsonLogger handle `debug` and `info` as `stdout` and
 `warning`, `critical`, `exception` and `error` as `stderr`.

``` python

from simple_json_logger import JsonLogger


def foo():
    logger = JsonLogger()

    logger.debug("I'm a json in stdout !")
    logger.info("I'm a json in stdout !")

    logger.warning("I'm a json in stderr !")
    logger.error("Wow i'm json in stderr !")
    logger.critical("Wow i'm json in stderr !")

foo()
>>> {"msg": "I'm a json in stdout !", "logged_at": "2017-03-31T02:37:46.616014", "line_number": 7, "function": "foo", "level": "DEBUG", "file_path": "/Volumes/partition2/Users/diogo/PycharmProjects/simple_json_logger/bla.py"}
>>> {"msg": "I'm a json in stdout !", "logged_at": "2017-03-31T02:37:46.616145", "line_number": 8, "function": "foo", "level": "INFO", "file_path": "/Volumes/partition2/Users/diogo/PycharmProjects/simple_json_logger/bla.py"}
>>> {"msg": "Wow i'm json in stderr !", "logged_at": "2017-03-31T02:37:46.616225", "line_number": 9, "function": "foo", "level": "WARNING", "file_path": "/Volumes/partition2/Users/diogo/PycharmProjects/simple_json_logger/bla.py"}
>>> {"msg": "Wow i'm json in stderr !", "logged_at": "2017-03-31T02:37:46.616298", "line_number": 11, "function": "foo", "level": "ERROR", "file_path": "/Volumes/partition2/Users/diogo/PycharmProjects/simple_json_logger/bla.py"}
>>> {"msg": "Wow i'm json in stderr !", "logged_at": "2017-03-31T02:37:46.616369", "line_number": 12, "function": "foo", "level":  "CRITICAL", "file_path": "/Volumes/partition2/Users/diogo/PycharmProjects/simple_json_logger/bla.py"}
```

 You may override that behavior by passing your own `stream` handler.

 ``` python

 import sys
 from simple_json_logger import JsonLogger


 logger = JsonLogger(stream=sys.stdout)

 logger.error("I'll always log to stdout!!!")
 >>> {"msg": "I'll always log to stdout!!!", "logged_at": "2017-03-31T02:43:44.883072", "line_number": 5, "function": "<module>", "level": "ERROR", "file_path": "/Volumes/partition2/Users/diogo/PycharmProjects/simple_json_logger/bla.py"}

 ```

### It logs everything

``` python
from simple_json_logger import JsonLogger
from datetime import datetime

logger = JsonLogger()
logger.info({
    'date_objects': datetime.now(),
    'exceptions': KeyError("Boooom"),
    'types': JsonLogger
})
>>> {"msg": {"date_objects": "2017-03-31T03:17:33.898880", "exceptions": "Exception: 'Boooom'", "types": "<class 'simple_json_logger.logger.JsonLogger'>"}, "logged_at": "2017-03-31T03:17:33.900136", "line_number": 8, "function": "<module>", "level": "INFO", "file_path": "/Volumes/partition2/Users/diogo/PycharmProjects/simple_json_logger/bla.py"}
```

`Callable[[], str]` log values may also be used to generate dynamic content that
are evaluated at serialization time:

```python
from random import randint
from simple_json_logger import JsonLogger


logger = JsonLogger(extra={"random_number": lambda: randint(1, 100)})

logger.info("First log line")
# {"logged_at": "2018-02-06T13:55:35.439355", "line_number": 1, "function": "<module>", "level": "INFO", "file_path": "<input>", "msg": "First log line", "random_number": 6}

logger.info("Second log line")
# {"logged_at": "2018-02-06T13:55:35.439590", "line_number": 2, "function": "<module>", "level": "INFO", "file_path": "<input>", "msg": "Second log line", "random_number": 48}

``` 

### Adding content to root

By default, everything passed to the log methods is inserted inside
the `msg` root attribute, but sometimes we want to add content to the root level.
For this, we may use the `extra` or `flatten` parameters.

#### Extra

``` python
from simple_json_logger import JsonLogger


logger = JsonLogger()


def foo():
    a = 69
    b = 666
    c = [a, b]
    logger.info("I'm a simple log", extra={'local_context': locals()})

if __name__ == '__main__':
    foo()

>>> {"msg": "I'm a simple log", "logged_at": "2017-08-11T12:15:56.461348", "line_number": 11, "function": "foo", "level": "INFO", "path": "/Users/diogo/PycharmProjects/simple_json_logger/bla.py", "local_context": {"c": [69, 666], "b": 666, "a": 69}}
```

The `extra` parameter also allow you to override the default root content:

``` python
from simple_json_logger import JsonLogger


logger = JsonLogger()

logger.info("I'm a simple log")
>>> {"msg": "I'm a simple log", "logged_at": "2017-08-11T12:21:05.722216", "line_number": 5, "function": "<module>", "level": "INFO", "path": "/Users/diogo/PycharmProjects/simple_json_logger/bla.py"}

logger.info("I'm a simple log", extra={'logged_at': 'Yesterday'})
>>> {"msg": "I'm a simple log", "logged_at": "Yesterday", "line_number": 6, "function": "<module>", "level": "INFO", "path": "/Users/diogo/PycharmProjects/simple_json_logger/bla.py"}
```

and it may also be used as an instance attribute:

``` python
from simple_json_logger import JsonLogger


logger = JsonLogger(extra={'logged_at': 'Yesterday'})

logger.info("I'm a simple log")
>>> {"msg": "I'm a simple log", "logged_at": "Yesterday", "line_number": 6, "function": "<module>", "level": "INFO", "path": "/Users/diogo/PycharmProjects/simple_json_logger/bla.py"}

logger.info("I'm a simple log")
>>> {"msg": "I'm a simple log", "logged_at": "Yesterday", "line_number": 6, "function": "<module>", "level": "INFO", "path": "/Users/diogo/PycharmProjects/simple_json_logger/bla.py"}
```

#### Flatten

Alternatively, this behavior may be achieved using `flatten`. Which is
available both as a method parameter and instance attribute.

As an instance attribute, every call to a log method would "flat" the dict attributes.

``` python
from simple_json_logger import JsonLogger


logger = JsonLogger(flatten=True)

logger.info({"status_code": 200, "response_time": 0.00534534})
>>> {"status_code": 200, "response_time": 0.534534, "logged_at": "2017-08-11T16:18:58.446985", "line_number": 6, "function": "<module>", "level": "INFO", "path": "/Users/diogo/PycharmProjects/simple_json_logger/bla.py"}

logger.error({"status_code": 404, "response_time": 0.00134534})
>>> {"status_code": 200, "response_time": 0.534534, "logged_at": "2017-08-11T16:18:58.446986", "line_number": 6, "function": "<module>", "level": "INFO", "path": "/Users/diogo/PycharmProjects/simple_json_logger/bla.py"}
```

As a method parameter, only the specific call would add the content to the root.

``` python
from simple_json_logger import JsonLogger


logger = JsonLogger()

logger.info({"status_code": 200, "response_time": 0.00534534}, flatten=True)
>>> {"logged_at": "2017-08-11T16:23:16.312441", "line_number": 6, "function": "<module>", "level": "INFO", "path": "/Users/diogo/PycharmProjects/simple_json_logger/bla.py", "status_code": 200, "response_time": 0.00534534}

logger.error({"status_code": 404, "response_time": 0.00134534})
>>> {"logged_at": "2017-08-11T16:23:16.312618", "line_number": 8, "function": "<module>", "level": "ERROR", "path": "/Users/diogo/PycharmProjects/simple_json_logger/bla.py", "msg": {"status_code": 404, "response_time": 0.00134534}}
```

**Warning**: It is possible to overwrite keys that are already present at root level.

``` python
from simple_json_logger import JsonLogger


logger = JsonLogger()

logger.info({'logged_at': 'Yesterday'}, flatten=True)
>>> {"logged_at": "Yesterday", "line_number": 6, "function": "<module>", "level": "INFO", "path": "/Users/diogo/PycharmProjects/simple_json_logger/bla.py"}
```

#### Exclude default logger fields

If you think that the default fields are too much, it's also possible to 
exclude fields from the output message. 

``` python
from simple_json_logger import JsonLogger


logger = JsonLogger(exclude_fields=['function',
                                    'logged_at',
                                    'file_path',
                                    'line_number'])
logger.info("Function, file path and line number wont be printed")
>>> {"level": "INFO", "msg": "Function, file path and line number wont be printed"}

```

### Serializer options

`serializer_kwargs` is available both as instance attribute and as
a log method parameter and may be used to pass keyword arguments to the
`serializer` function. (See more: https://docs.python.org/3/library/json.html)

For pretty printing the output, you may use the `indent` kwarg. Ex.:

```python
from simple_json_logger import JsonLogger


logger = JsonLogger(serializer_kwargs={'indent': 4})

logger.info({'artist': 'Black Country Communion', 'song': 'Cold'})

```
Would result in a pretty indented output:

``` javascript
{
    "logged_at": "2017-08-11T21:04:21.559070",
    "line_number": 5,
    "function": "<module>",
    "level": "INFO",
    "file_path": "/Users/diogo/Library/Preferences/PyCharm2017.1/scratches/scratch_32.py",
    "msg": {
        "artist": "Black Country Communion",
        "song": "Cold"
    }
}
```

The same result can be achieved making a log call with `serializer_kwargs`
as a parameter.

```python
logger.warning({'artist': 'Black Country Communion', 'song': 'Cold'},
               serializer_kwargs={'indent': 4})
```


## Compatibility

It is granted to work and tested on python >=3.3. Even through it's
untested, it probably works on python 2.7, but use at your own risk.

## Depencencies

Has none.
