from fastapi import HTTPException, status
from datetime import datetime
import uuid
from pydantic import BaseModel, field_validator
from gen_protoc.events.test_events_pb2 import TestEvent, YetAnotherTestEvent


# TODO: Should it be moved to another file?
events_mapping = {
    "test_event_name": TestEvent,
    "test_event_name_2": YetAnotherTestEvent,
}


# TODO: Should it be moved to another file?
def is_valid_date(datetime_to_check_int: int, 
                  datetime_field_name: str = "sent_at"
                  ):
    
    datetime_to_check = datetime.utcfromtimestamp(datetime_to_check_int)
    current_date_time = datetime.now()
    if datetime_to_check > current_date_time:
        check = False
        message = f"{datetime_field_name} datetime {datetime_to_check} is too far in future"
    elif datetime_to_check_int < 0:
        check = False
        message = f"{datetime_field_name} datetime {datetime_to_check} should be later than January 1, 1970"
    else:
        check = True
        message = None
    return (check, message)


class RequestEventContext(BaseModel):
    sent_at: int
    received_at: int
    processed_at: int
    message_id: str
    user_agent: str

    @field_validator('sent_at', 'received_at', 'processed_at')
    def datetime_check(cls, v):
        datetime_check, message = is_valid_date(v)
        if not datetime_check:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=message
            )   
        return v
    
    @field_validator('message_id')
    def message_id_check(cls, v):
        try:
            uuid_obj = uuid.UUID(v)
            return v
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"message_id {v} is not in UUID format"
                )
        
    @field_validator('user_agent')
    def user_agent_check(cls, v):
        if not v:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"user_agent field should not be empty"
            )
        return v


class RequestEventItem(BaseModel):
    event_name: str
    context: RequestEventContext
    data: dict

    @field_validator('event_name')
    def event_name_check(cls, v):
        event_names = list(events_mapping.keys())
        if v not in event_names:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"event_name {v} is not supported"
            )
        return v