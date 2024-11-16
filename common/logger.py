import datetime
import json
import logging
import os
import traceback
from types import TracebackType
from typing import Any, Mapping, Optional, Tuple, Type, Union

from version import get_version_from_pyproject

APP_NAME = "event-collector"
APP_VERSION = get_version_from_pyproject()


class ExtraLogger(logging.Logger):
    """
    A custom logger class extending Python's built-in `logging.Logger`.

    Adds additional flexibility by allowing extra fields to be attached
    to each log record. It overrides the `makeRecord` method to enable custom attributes.
    """

    def makeRecord(  # type: ignore
        self,
        name: str,
        level: int,
        fn: str,
        lno: int,
        msg: object,
        args: (Union[Tuple[object, ...], Mapping[str, object]]),
        exc_info: Union[
            Tuple[Type[BaseException], BaseException, Optional[TracebackType]],
            Tuple[None, None, None],
        ],
        func: Optional[str] = ...,  # type: ignore
        extra: Optional[Mapping[str, object]] = ...,  # type: ignore
        sinfo: Optional[str] = ...,  # type: ignore
    ) -> logging.LogRecord:
        """
        Creates a log record, allowing custom `extra` data for richer log context.

        Args:
            name (str): Name of the logger.
            level (int): The log level for the logger.
            fn (str): The source filename of the logging call.
            lno (int): The line number in the source file where the logging call was made.
            msg (object): The log message.
            args (Union[Tuple[object, ...], Mapping[str, object]]): Arguments for the log message.
            exc_info (Union[Tuple[Type[BaseException], BaseException, Optional[TracebackType]],
                Tuple[None, None, None]]): Exception information for logging.
            func (Optional[str]): The function name where the logging call was made.
            extra (Optional[Mapping[str, object]]): Additional context information to attach to the log record.
            sinfo (Optional[str]): Stack information.

        Returns:
            logging.LogRecord: log record, allowing custom `extra` data for richer log context.
        """
        record = super().makeRecord(
            name,
            level,
            fn,
            lno,
            msg,
            args,
            exc_info,
            func=func,
            extra=None,
            sinfo=sinfo,
        )
        record._extra = extra  # type: ignore
        return record


class DateTimeEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for serializing `datetime` and `timedelta` objects.
    Extends `json.JSONEncoder` to handle `datetime.datetime`, `datetime.date`,
    `datetime.time`, and `datetime.timedelta` types by converting them to ISO 8601 format strings.
    """

    def default(self, obj: Any) -> Any:
        """
        Converts recognized types to ISO 8601 formatted strings.

        Args:
            obj (Any): The object to serialize.
        Returns:
            str: The ISO 8601 string representation of the `datetime` or `timedelta` object, or the
                default JSON encoding for unsupported types.
        """
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()
        elif isinstance(obj, datetime.timedelta):
            return (datetime.datetime.min + obj).time().isoformat()

        return super(DateTimeEncoder, self).default(obj)


class JSONFormatter(logging.Formatter):
    """
    A custom logging formatter that outputs log records in JSON format.
    Structures log records with the log level, timestamp in UTC, and application-specific
    metadata, including the release ID, message content, and optional tracebacks for errors.
    """

    def __init__(self):
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        """
        Formats a log record into a JSON string.

        Args:
            record (logging.LogRecord): The log record to format.
        Returns:
            str: A JSON-formatted string representing the log record.
        """
        log_dict = {
            "level": record.levelname,
            "timestamp": datetime.datetime.fromtimestamp(record.created, tz=datetime.timezone.utc),
            "app": {
                "name": record.name,
                "releaseId": APP_VERSION,
                "message": record.getMessage(),
                "extra": record._extra,  # type: ignore
            },
        }

        if record.levelno > logging.INFO:
            log_dict.update(
                {
                    "thread": record.thread,
                    "traceback": traceback.format_exception(*record.exc_info) if record.exc_info else None,
                }
            )

        json_formatted = json.dumps(log_dict, cls=DateTimeEncoder)

        return json_formatted


class MultiLevelFilter(logging.Filter):
    """
    Custom filter to allow multiple log levels.
    """

    def __init__(self, levels):
        super().__init__()
        self.levels = levels

    def filter(self, record):
        return record.levelno in self.levels


def get_logger(name: str = APP_NAME) -> logging.Logger:
    """
    Configures and returns an instance of `ExtraLogger` with JSON formatting.

    Logs:
        logging.Logger: The configured `ExtraLogger` instance for logging in JSON format.
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.setLoggerClass(ExtraLogger)
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    loggingStreamHandler = logging.StreamHandler()
    loggingStreamHandler.setFormatter(JSONFormatter())
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.addHandler(loggingStreamHandler)
    logger.propagate = False
    return logger
