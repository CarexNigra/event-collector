import json
import traceback
import uuid
from datetime import datetime, timedelta
from typing import Any, List, Optional

from confluent_kafka import Consumer, Message
from google.protobuf.json_format import MessageToJson

from common.logger import get_logger
from config.config import KafkaConsumerProperties, get_config
from consumer.file_writers import FileWriterBase
from events_registry.events_registry import events_mapping
from events_registry.key_manager import ProducerKeyManager

logger = get_logger()

# ==================================== #
# (1) Create consumer instance
# ==================================== #


def create_kafka_consumer(config: Optional[dict[str, Any]] = None) -> Consumer:
    """
    Creates a Kafka Consumer instance with a specified or default configuration.
    Args:
        config (Optional[dict[str, Any]]): Kafka consumer configuration.
                                           If None, the default configuration is used.
    Returns:
        Consumer: The configured Kafka consumer instance.
    """
    if not config:
        config = get_config()["consumer"]
    logger.info(f"Kafka consumer raw config: {config}")
    kafka_consumer_config = KafkaConsumerProperties(**config)
    kafka_consumer_config_dict = kafka_consumer_config.model_dump(by_alias=True)
    logger.info(f"Kafka consumer config dict: {kafka_consumer_config_dict}")
    return Consumer(**kafka_consumer_config_dict)


# ==================================== #
# (2) Parse messages from kafka
# ==================================== #


def parse_message(message: Message) -> dict[str, Any]:
    """
    Parses a message from Kafka to extract its event data.

    Args:
        message (Message): The Kafka message to parse (binary).
    Returns:
        dict[str, Any]: Parsed message data in dictionary format.
    """
    key = message.key()

    if isinstance(key, bytes):
        event_type = ProducerKeyManager(producer_key=key.decode("utf-8")).get_event_type_from_key()
    else:
        raise ValueError("Message key must be bytes to decode.")

    binary_value = message.value()

    if event_type in events_mapping:
        event_class = events_mapping.get(event_type)
        if event_class is None:
            logger.info(f"Event type '{event_type}' not found in events_mapping.")
            return {}
        else:
            event = event_class()
            event.ParseFromString(binary_value)
            event_json_string = MessageToJson(event)
            event_json_data = json.loads(event_json_string)
            logger.info(f"(2) Parsing. Event class data type: {type(event_json_data)}, data: {event_json_data}")
            return event_json_data
    else:
        return {}


# ==================================== #
# (3) Set up EventConsumer
# ==================================== #


class EventConsumer:
    def __init__(
        self,
        file_writer: FileWriterBase,
        consumer: Consumer,
        consumer_group_id: str,
        topics: List[str],
        max_output_file_size: int,
        flush_interval: int,
    ) -> None:
        """
        Class representing a Kafka consumer that consumes events and writes them to storage.

        Args:
            file_writer (FileWriterBase): Writer used for saving events to storage.
            consumer (Consumer): Kafka consumer instance for consuming messages.
            consumer_group_id (str): ID for the Kafka consumer group.
            topics (List[str]): List of topics to subscribe to.
            max_output_file_size (int): Maximum file size (with messages batch) in bytes before flushing to storage.
            flush_interval (int): Time interval in seconds to flush messages to storage
                (even if max_output_file_size is not reached)
        Attributes:
            _message_queue (List[str]): In-memory queue for holding messages (deseiralized to str).
            _last_flush_time (datetime): Timestamp of the last message flush.
            _running (bool): Flag to control the message consumption loop.
            _unique_consumer_id (str): Unique identifier for the consumer instance. Needed to be added
                to the file name (to force different consumers' writing to different files)
        """
        self._file_writer = file_writer
        self._consumer = consumer
        self._topics = topics
        self._max_output_file_size = max_output_file_size
        self._flush_interval = timedelta(seconds=flush_interval)
        self._message_queue: list[str] = []
        self._last_flush_time = datetime.now()
        self._running = True

        consumer_id = consumer.memberid()
        if not consumer_group_id or not consumer_id:
            self._unique_consumer_id = str(uuid.uuid4())
        else:
            self._unique_consumer_id = f"{consumer_group_id}_{consumer_id}"

    def stop(self) -> None:
        """
        Stops the consumer's event consumption loop and flush remaining messages.
        """
        self._running = False
        self._flush_messages()

    def _flush_messages(self) -> None:
        """
        Flushes the in-memory message queue to storage and commit offsets in Kafka.
        """
        logger.info(f"(3) Flushing {len(self._message_queue)} parsed messages.")
        self._file_writer.write_file(self._message_queue, self._unique_consumer_id)
        self._consumer.commit(asynchronous=True)  # Commit offsets after writing
        self._message_queue = []

    def run_consume_loop(self) -> None:
        """
        Starts the event consumption loop, process messages, and flush them to storage based on
        file size or time interval thresholds.
        """
        queue_size_bytes = 0
        unqiue_msgs = set()

        try:
            self._consumer.subscribe(self._topics)

            while self._running:  # Added to stop the loop
                raw_msg = self._consumer.poll(timeout=1.0)
                # (1) Waits for up to 1 second before returning None if no message is available.
                logger.info(f"(1) Consumption. Message: {raw_msg}")

                if raw_msg is None:
                    continue

                if raw_msg.error():
                    logger.info("(1) Consumption. Kafka message error")

                try:
                    if raw_msg not in unqiue_msgs:
                        # (2) Parse message
                        msg_dict = parse_message(raw_msg)
                        msg_str = json.dumps(msg_dict)
                        msg_size = len((msg_str + "\n").encode("utf-8"))

                        # (3) No flushing conditions, message is added to queue
                        if queue_size_bytes + msg_size <= self._max_output_file_size:
                            self._message_queue.append(msg_str)
                            queue_size_bytes += msg_size
                            unqiue_msgs.add(raw_msg)

                        # (4) Flushing option by queue size, message added to empty queue after flushing
                        else:
                            self._flush_messages()
                            self._message_queue.append(msg_str)
                            queue_size_bytes = msg_size
                            unqiue_msgs = set([raw_msg])

                        # (5) Flushing option by time
                        current_time = datetime.now()
                        if current_time - self._last_flush_time >= self._flush_interval:
                            self._flush_messages()
                            self._last_flush_time = current_time
                            queue_size_bytes = 0
                            unqiue_msgs = set()

                except Exception:
                    stack_trace = traceback.format_exc()
                    logger.error(f"(2) Parsing. Error parsing message: {raw_msg}. Exception: {stack_trace}")
                    # (6) Continue with next message, do not stop processing

        finally:
            # (7) Close down consumer to commit final offsets.
            self._flush_messages()
            self._consumer.close()