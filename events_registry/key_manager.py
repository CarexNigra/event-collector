import uuid


class ProducerKeyManager:
    def __init__(self, event_type=None, producer_key=None) -> None:
        self.event_type = event_type
        self.producer_key = producer_key

    def generate_key(self) -> str:
        producer_key = (
            self.event_type + "_" + str(uuid.uuid4())
        )  # TODO: Is it the right order? Should it affect partitioning?
        return producer_key

    def get_event_type_from_key(self) -> str:
        parts = self.producer_key.split("_", 1)

        if len(parts) < 2:
            raise ValueError("Input string is not in the expected format.")

        event_type = parts[0]
        return event_type
