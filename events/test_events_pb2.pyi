from typing import ClassVar as _ClassVar
from typing import List as _List
from typing import Mapping as _Mapping
from typing import Optional as _Optional
from typing import Union as _Union

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message

# from google.protobuf import descriptor_pb2 as _descriptor_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper

from events import context_pb2 as _context_pb2

DESCRIPTOR: _descriptor.FileDescriptor

class UserRole(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__: _List[str] = []
    OWNER: _ClassVar[UserRole]
    EDITOR: _ClassVar[UserRole]
    VIEWER: _ClassVar[UserRole]

class ObjectType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__: _List[str] = []
    CARD: _ClassVar[ObjectType]
    STICKY_NOTE: _ClassVar[ObjectType]
    TEXT: _ClassVar[ObjectType]
    IMAGE: _ClassVar[ObjectType]

class InputType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__: _List[str] = []
    SIMPLE_SELECT: _ClassVar[InputType]
    MOVE: _ClassVar[InputType]
    ROTATE: _ClassVar[InputType]
    SCALE: _ClassVar[InputType]

OWNER: UserRole
EDITOR: UserRole
VIEWER: UserRole
CARD: ObjectType
STICKY_NOTE: ObjectType
TEXT: ObjectType
IMAGE: ObjectType
SIMPLE_SELECT: InputType
MOVE: InputType
ROTATE: InputType
SCALE: InputType
EVENT_NAME_FIELD_NUMBER: int
event_name: _descriptor.FieldDescriptor

class TestEvent(_message.Message):
    __slots__ = ["context", "user_id", "account_id", "user_role"]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    ACCOUNT_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ROLE_FIELD_NUMBER: _ClassVar[int]
    context: _context_pb2.EventContext
    user_id: str
    account_id: str
    user_role: UserRole
    def __init__(
        self,
        context: _Optional[_Union[_context_pb2.EventContext, _Mapping]] = ...,
        user_id: _Optional[str] = ...,
        account_id: _Optional[str] = ...,
        user_role: _Optional[_Union[UserRole, str]] = ...,
    ) -> None: ...

class YetAnotherTestEvent(_message.Message):
    __slots__ = ["context", "input_type", "object_id", "object_type"]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    INPUT_TYPE_FIELD_NUMBER: _ClassVar[int]
    OBJECT_ID_FIELD_NUMBER: _ClassVar[int]
    OBJECT_TYPE_FIELD_NUMBER: _ClassVar[int]
    context: _context_pb2.EventContext
    input_type: InputType
    object_id: str
    object_type: ObjectType
    def __init__(
        self,
        context: _Optional[_Union[_context_pb2.EventContext, _Mapping]] = ...,
        input_type: _Optional[_Union[InputType, str]] = ...,
        object_id: _Optional[str] = ...,
        object_type: _Optional[_Union[ObjectType, str]] = ...,
    ) -> None: ...
