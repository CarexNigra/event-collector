# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: events/test_events.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from events import context_pb2 as events_dot_context__pb2
from google.protobuf import descriptor_pb2 as google_dot_protobuf_dot_descriptor__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x18\x65vents/test_events.proto\x12\x06\x65vents\x1a\x14\x65vents/context.proto\x1a google/protobuf/descriptor.proto\"\xc5\x01\n\tTestEvent\x12*\n\x07\x63ontext\x18\x01 \x01(\x0b\x32\x14.events.EventContextH\x00\x88\x01\x01\x12\x14\n\x07user_id\x18\x02 \x01(\tH\x01\x88\x01\x01\x12\x17\n\naccount_id\x18\x03 \x01(\tH\x02\x88\x01\x01\x12(\n\tuser_role\x18\x04 \x01(\x0e\x32\x10.events.UserRoleH\x03\x88\x01\x01\x42\n\n\x08_contextB\n\n\x08_user_idB\r\n\x0b_account_idB\x0c\n\n_user_role\"\xec\x01\n\x13YetAnotherTestEvent\x12*\n\x07\x63ontext\x18\x01 \x01(\x0b\x32\x14.events.EventContextH\x00\x88\x01\x01\x12*\n\ninput_type\x18\x02 \x01(\x0e\x32\x11.events.InputTypeH\x01\x88\x01\x01\x12\x16\n\tobject_id\x18\x03 \x01(\tH\x02\x88\x01\x01\x12,\n\x0bobject_type\x18\x04 \x01(\x0e\x32\x12.events.ObjectTypeH\x03\x88\x01\x01\x42\n\n\x08_contextB\r\n\x0b_input_typeB\x0c\n\n_object_idB\x0e\n\x0c_object_type*-\n\x08UserRole\x12\t\n\x05OWNER\x10\x00\x12\n\n\x06\x45\x44ITOR\x10\x01\x12\n\n\x06VIEWER\x10\x02*<\n\nObjectType\x12\x08\n\x04\x43\x41RD\x10\x00\x12\x0f\n\x0bSTICKY_NOTE\x10\x01\x12\x08\n\x04TEXT\x10\x02\x12\t\n\x05IMAGE\x10\x03*?\n\tInputType\x12\x11\n\rSIMPLE_SELECT\x10\x00\x12\x08\n\x04MOVE\x10\x01\x12\n\n\x06ROTATE\x10\x02\x12\t\n\x05SCALE\x10\x03:5\n\nevent_name\x12\x1f.google.protobuf.MessageOptions\x18\xd0\x86\x03 \x01(\tb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'events.test_events_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_USERROLE']._serialized_start=531
  _globals['_USERROLE']._serialized_end=576
  _globals['_OBJECTTYPE']._serialized_start=578
  _globals['_OBJECTTYPE']._serialized_end=638
  _globals['_INPUTTYPE']._serialized_start=640
  _globals['_INPUTTYPE']._serialized_end=703
  _globals['_TESTEVENT']._serialized_start=93
  _globals['_TESTEVENT']._serialized_end=290
  _globals['_YETANOTHERTESTEVENT']._serialized_start=293
  _globals['_YETANOTHERTESTEVENT']._serialized_end=529
# @@protoc_insertion_point(module_scope)