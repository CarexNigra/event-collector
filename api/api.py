from fastapi import Depends, FastAPI, HTTPException, Request, Response, status

from api.producer import create_kafka_producer, delivery_report
from api.request import RequestEventItem
from common.logger import get_logger
from config.config import get_producer_config
from events.context_pb2 import EventContext
from events_registry.events_registry import events_mapping
from events_registry.key_manager import ProducerKeyManager

logger = get_logger("api")

app = FastAPI()


@app.post("/store", response_model=None)
async def store_event(
    request: Request,
    response: Response,
    event_item: RequestEventItem,
    kafka_producer=Depends(create_kafka_producer),
    config=Depends(get_producer_config),
) -> None:
    """
    Endpoint to receive and store an event in Kafka.
    This endpoint handles event submission, processes the event data, and
    publishes it to a specified Kafka topic.

    Args:
        request (Request): The FastAPI request object.
        response (Response): The FastAPI response object for setting the status code.
        event_item (RequestEventItem): The event data to be processed and published.
        kafka_producer: Kafka producer dependency.
        config: Configuration dependency for accessing general properties.
    Raises:
        HTTPException: If the content type is unsupported, or the event name is unknown.
        415 error if the content type is not supported
        204 if successful event publishing
    """
    # (1) Validate content type of the body
    content_type = request.headers.get("content-type", None)
    if content_type != "application/json":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=f"Unsupported media type {content_type}"
        )

    if event_item.event_name in events_mapping:
        # (2) Create Event object
        event_class = events_mapping.get(event_item.event_name)
        event_context = EventContext(**event_item.context.model_dump())  # it is a dict
        if event_class is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown event name: {event_item.event_name}"
            )
        else:
            event_instance = event_class(
                context=event_context,
                **event_item.data,
            )

        # (3) Serialize Event object
        serialized_event = event_instance.SerializeToString()

        # (4) Generate producer key
        key_manager = ProducerKeyManager(event_type=event_item.event_name)
        producer_key = key_manager.generate_key()
        logger.debug(f"Producer key: {producer_key}")

        kafka_topic = config.app.kafka_topic

        # (5) Send serialized_event to Kafka
        kafka_producer.produce(
            topic=kafka_topic,
            value=serialized_event,
            key=producer_key,
            on_delivery=delivery_report,
        )
        # Trigger the on_delivery callback
        kafka_producer.poll(0)

        # (5) Return 204
        response.status_code = status.HTTP_204_NO_CONTENT

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown event name: {event_item.event_name}"
        )
