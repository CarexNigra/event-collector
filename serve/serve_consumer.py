from consumer.event_consumer import create_kafka_consumer, EventConsumer
from consumer.file_writers import MinioFileWriter, create_bucket, create_minio_client

from config.config import get_config

# (1) Get general properties
general_config_dict = get_config()['general']
consumer_config_dict = get_config()['consumer']

# Instantiate Minio file writer
minio_client = create_minio_client()
create_bucket(general_config_dict["root_path"], minio_client)
file_writer = MinioFileWriter(
    root_path=general_config_dict["root_path"],
    minio_client=minio_client,
)

# (3) Instantiate consumer
consumer = create_kafka_consumer()
event_consumer = EventConsumer(
    file_writer=file_writer,
    consumer=consumer,
    consumer_group_id=consumer_config_dict['group_id'],
    topics=[general_config_dict["kafka_topic"]],
    max_output_file_size = general_config_dict["max_output_file_size"], 
    flush_interval = general_config_dict["flush_interval"],
)

# (4) Write
event_consumer.run_consume_loop()