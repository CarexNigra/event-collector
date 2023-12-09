import uuid
from pydantic import BaseModel
from gen_protoc.events.test_events_pb2 import EventContext, TestEvent, YetAnotherTestEvent


class RequestEventContext(BaseModel):
    sent_at: int 
    received_at: int
    processed_at: int
    message_id: str
    user_agent: str

class RequestEventItem(BaseModel):
    event_name: str
    context: RequestEventContext
    data: dict

events_mapping = {
    "test_event_name": TestEvent,
    "test_event_name_2": YetAnotherTestEvent
}

event_item = RequestEventItem(
    event_name="test_event_name",
    context=RequestEventContext(
        sent_at=1701530942,
        received_at=1701530942,
        processed_at=1701530942,
        message_id=str(uuid.uuid4()),
        user_agent="some_user_agent",
    ),
    data={
        "user_id": "some_user_id",
        "account_id": "some_account_id",
         "user_role": "OWNER",
    })


if event_item.event_name in events_mapping:
    event_class = events_mapping.get(event_item.event_name)
    print("Class:", event_class)

    context = EventContext(**event_item.context.model_dump())
    event_instance = event_class(
        context=context,
        event_name=event_item.event_name,
        **event_item.data,
    )

    # (6) Serialize Event object
    serialized_event = event_instance.SerializeToString()
    print(serialized_event)
    