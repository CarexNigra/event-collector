from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class EventContext(_message.Message):
    __slots__ = ["sent_at", "received_at", "processed_at", "message_id", "user_agent"]
    SENT_AT_FIELD_NUMBER: _ClassVar[int]
    RECEIVED_AT_FIELD_NUMBER: _ClassVar[int]
    PROCESSED_AT_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_ID_FIELD_NUMBER: _ClassVar[int]
    USER_AGENT_FIELD_NUMBER: _ClassVar[int]
    sent_at: int
    received_at: int
    processed_at: int
    message_id: str
    user_agent: str
    def __init__(self, sent_at: _Optional[int] = ..., received_at: _Optional[int] = ..., processed_at: _Optional[int] = ..., message_id: _Optional[str] = ..., user_agent: _Optional[str] = ...) -> None: ...
