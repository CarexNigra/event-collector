from fastapi import FastAPI, HTTPException, Request, Response, status, Depends
from datetime import datetime
import uuid
from pydantic import BaseModel, field_validator
from gen_protoc.events.test_events_pb2 import EventContext, TestEvent, YetAnotherTestEvent
from confluent_kafka import Producer



##############################################
# PART 1: Event models
##############################################

events_mapping = {
    "test_event_name": TestEvent,
    "test_event_name_2": YetAnotherTestEvent,
}


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



##############################################
# PART 2: Kafka
##############################################
    
KAFKA_TOPIC = 'event_messages' 


#############
# Mock kafka object
#############
class KafkaProducerWrapper:
    def __init__(self, producer):
        self.producer = producer

    def produce(self, topic, event):
        self.producer.produce(topic, event)
        self.producer.flush()


def create_kafka_producer():
    kafka_producer_config = {"bootstrap.servers": "localhost:9092"} # TODO: I cannot figure out how to get rid of this dependency from config and fake in
    return KafkaProducerWrapper(Producer(kafka_producer_config))


#############
# In real life
#############
# # TODO: What should be the format of the topic name, are there any conventions?
# # Should we send all event types to one topic, or to different?

# kafka_producer_config = {
#     "bootstrap.servers": "localhost:9092", # TODO: What configs should be added here?
# }
# producer = Producer(kafka_producer_config) # TODO: Should I leave it here, or put inside the send_event funtion?


# def delivery_report(err, msg):
#     if err is not None:
#         print(f"Message delivery failed: {err}")
#     else:
#         print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")


# def send_event_to_kafka(topic: str, 
#                         event: bytes, # TODO: Which data type should be here, taking into account that we pass serialized event (bytes)
#                         callback=delivery_report): 
#     # Produce the event to the Kafka topic
#     producer.produce(topic, value=event)
#     # Flush the producer to ensure the message is sent
#     producer.flush()



##############################################
# PART 3: Handler
##############################################

app = FastAPI()


@app.post("/store", response_model=None)
async def store_event(request: Request, 
                      response: Response, 
                      event_item: RequestEventItem, 
                      kafka_producer: KafkaProducerWrapper = Depends(create_kafka_producer) # TODO: Why do we need "Depends"?
) -> None: 
    
    # (1) Check content type of the body
    content_type = request.headers.get("content-type", None)
    if content_type != "application/json":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=f"Unsupported media type {content_type}"
        )
    
    if event_item.event_name in events_mapping:
        # (2) Create Event object
        event_class = events_mapping.get(event_item.event_name)
        event_context = EventContext(**event_item.context.model_dump()) # Here we get context dict 
        event_instance = event_class(
            context = event_context,
            event_name = event_item.event_name,
            **event_item.data)
    
        # (3) Serialize Event object
        serialized_event = event_instance.SerializeToString()

        # (4) TODO: Send serialized_event to Kafka
        kafka_producer.produce(topic = KAFKA_TOPIC, event = serialized_event)
        
        # (5) Return 204
        response.status_code = status.HTTP_204_NO_CONTENT

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown event name: {event_item.event_name}"
        )
