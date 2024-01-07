from fastapi import FastAPI, HTTPException, Request, Response, status, Depends
from gen_protoc.events.test_events_pb2 import EventContext

from schemas import RequestEventItem, events_mapping
from kafka import create_kafka_producer, KAFKA_TOPIC


app = FastAPI()

@app.post("/store", response_model=None)
async def store_event(request: Request, 
                      response: Response, 
                      event_item: RequestEventItem,
                      kafka_producer = Depends(create_kafka_producer)
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