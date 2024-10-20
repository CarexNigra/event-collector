from fastapi import Depends, FastAPI, HTTPException, Request, Response, status

from api.producer import create_kafka_producer, delivery_report
from api.request import RequestEventItem
from config.config import get_config
from events.context_pb2 import EventContext
from events_registry.events_registry import events_mapping
from events_registry.key_manager import ProducerKeyManager

from common.logger import get_logger

logger = get_logger()

app = FastAPI()


@app.post("/store", response_model=None)
async def store_event(
    request: Request,
    response: Response,
    event_item: RequestEventItem,
    kafka_producer=Depends(create_kafka_producer),
    config=Depends(get_config),
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
        event_context = EventContext(**event_item.context.model_dump())  # Here we get context dict
        event_instance = event_class(
            context=event_context,
            **event_item.data,
        )

        # (3) Serialize Event object
        serialized_event = event_instance.SerializeToString()

        # (4) Generate key
        key_manager = ProducerKeyManager(event_type=event_item.event_name)
        producer_key = key_manager.generate_key()
        logger.info(f"Producer key: {producer_key}")

        # (4) Parse general properties config to later get kafka_topic from it
        general_config_dict = config['general']

        # (5) Send serialized_event to Kafka
        kafka_producer.produce(
            topic=general_config_dict["kafka_topic"],
            value=serialized_event,
            key=producer_key,
            on_delivery=delivery_report,
        )

        # (5) Return 204
        response.status_code = status.HTTP_204_NO_CONTENT

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown event name: {event_item.event_name}"
        )
