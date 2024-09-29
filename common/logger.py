import datetime
import json
import logging
import os
import traceback
from types import TracebackType
from typing import Mapping, Optional, Tuple, Type, Union

import pkg_resources  # type: ignore

app_name = "event-collector"
try:
    app_version = pkg_resources.get_distribution(app_name).version
except pkg_resources.DistributionNotFound:
    app_version = "undefined"


class ExtraLogger(logging.Logger):
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
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()
        elif isinstance(obj, datetime.timedelta):
            return (datetime.datetime.min + obj).time().isoformat()

        return super(DateTimeEncoder, self).default(obj)


class JSONFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()

    def format(self, record: logging.LogRecord):
        log_dict = {
            "level": record.levelname,
            "timestamp": datetime.datetime.utcfromtimestamp(record.created),
            "app": {
                "name": record.name,
                "releaseId": app_version,
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


def get_logger():
    logging.setLoggerClass(ExtraLogger)
    logger = logging.getLogger(app_name)
    if os.getenv("ENVIRONMENT", "dev"):
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    loggingStreamHandler = logging.StreamHandler()
    loggingStreamHandler.setFormatter(JSONFormatter())
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.addHandler(loggingStreamHandler)
    logger.propagate = False
    return logger