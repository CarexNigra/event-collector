import uuid


class ProducerKeyManager:
    """
    A manager class to generate and extract event-specific producer keys for partitioning purposes.

    Attributes:
        event_type (Optional[str]): The type of event to be included in the key.
        producer_key (Optional[str]): The unique producer key. Needed to balance load
           (helps kafka to define, which parition event is going to)
    """

    def __init__(self, event_type=None, producer_key=None) -> None:
        self.event_type = event_type
        self.producer_key = producer_key

    def generate_key(self) -> str:
        """
        Generates a unique producer key by concatenating the event type with a UUID.
        This key can be used to assist in partitioning messages by event type.

        Returns:
            str: A generated producer key in the format "<event_type>_<UUID>".
        """
        producer_key = (
            self.event_type + "_" + str(uuid.uuid4())
        )  # TODO: Is it the right order? Should it affect partitioning?
        return producer_key

    def get_event_type_from_key(self) -> str:
        """
        Extracts the event type from an existing producer key by splitting on the first underscore.

        Returns:
            str: The event type extracted from the producer key.
            ValueError: If the producer key is not in the expected "<event_type>_<UUID>" format.
        """
        parts = self.producer_key.split("_", 1)

        if len(parts) < 2:
            raise ValueError("Input string is not in the expected format.")

        event_type = parts[0]
        return event_type
