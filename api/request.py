import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from pydantic import BaseModel, field_validator

from events_registry.events_registry import events_mapping


def is_valid_date(datetime_to_check_int: int, datetime_field_name: str = "sent_at") -> tuple[bool, str | None]:
    """
    Validates if a given timestamp is in the past and later than January 1, 1970.

    Input:
        datetime_to_check_int (int): The timestamp to validate in Unix time format.
        datetime_field_name (str): The name of the field being validated (default: "sent_at").

    Output:
        tuple[bool, str | None]: A tuple with a boolean indicating validity and an
        optional error message if the timestamp is invalid.
    """

    datetime_to_check = datetime.fromtimestamp(datetime_to_check_int, tz=timezone.utc)
    current_date_time = datetime.now(timezone.utc)
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
    """
    Represents the context of an event request with validation on specific fields.

    Attributes:
        sent_at (int): The Unix timestamp indicating when the event was sent.
        received_at (int): The Unix timestamp indicating when the event was received.
        processed_at (int): The Unix timestamp indicating when the event was processed.
        message_id (str): A unique identifier for the message in UUID format.
        user_agent (str): Information about the user agent associated with the event.
    """

    @field_validator("sent_at", "received_at", "processed_at")
    def datetime_check(cls, v: int) -> int:
        """
        Ensures timestamps are valid and not in the future or before January 1, 1970.
        """
        datetime_check, message = is_valid_date(v)
        if not datetime_check:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
        return v

    @field_validator("message_id")
    def message_id_check(cls, v: str) -> str:
        """
        Ensures message_id is a valid UUID
        """
        try:
            uuid_obj = uuid.UUID(v)  # noqa: F841
            return v
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"message_id {v} is not in UUID format")

    @field_validator("user_agent")
    def user_agent_check(cls, v: str) -> str:
        """
        Ensures that `user_agent` is not empty.
        """
        if not v:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_agent field should not be empty")
        return v


class RequestEventItem(BaseModel):
    event_name: str
    context: RequestEventContext
    data: dict
    """
    Represents an event item request with validation on event name and context.

    Attributes:
        event_name (str): The name of the event, which must be in the `events_mapping` registry.
        context (RequestEventContext): Contextual information about the event, including 
                                    timestamps and identifiers.
        data (dict): Additional data associated with the event.
    """

    @field_validator("event_name")
    def event_name_check(cls, v: str) -> str:
        """
        Checks if the event name is valid and exists in events_mapping

        Raises:
            HTTPException: Raised if `event_name` is not supported.
        """
        event_names = list(events_mapping.keys())
        if v not in event_names:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"event_name {v} is not supported")
        return v
