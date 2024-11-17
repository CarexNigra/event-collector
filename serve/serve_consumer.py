from config.config import get_consumer_config
from consumer.event_consumer import EventConsumer, create_kafka_consumer
from consumer.file_writers.minio import MinioFileWriter, create_minio_client

# (1) Get general properties
config = get_consumer_config()

# (2) Instantiate Minio file writer
minio_client = create_minio_client()

file_writer = MinioFileWriter(
    root_path=config.app.root_path,
    minio_client=minio_client,
)

# (3) Create bucket in minio
file_writer.create_bucket()

# (4) Instantiate consumer
consumer = create_kafka_consumer()
event_consumer = EventConsumer(
    file_writer=file_writer,
    consumer=consumer,
    consumer_group_id=config.kafka.group_id,
    topics=[config.app.kafka_topic],
    max_output_file_size=config.app.max_output_file_size,
    flush_interval=config.app.flush_interval,
)

# (5) Write
event_consumer.run_consume_loop()
