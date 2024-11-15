# Event Collector  

The `event-collector` is a set of simple and scalable applications designed to manage consumption and initial storage of analytic events. Built to leverage Kafka and MinIO, this service handles both the production and consumption of event data, providing a structured way to ingest, process, and store information. 

**Table of Contents**
- [Key Components](#key-components)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Testing](#testing)
- [Next steps](#next-steps)
- [License](#license)


## Key Components
**Event registry**
*Event Registy* is a core component that handles serialization and deserialization of event data upon the dispatch of events to Kafka and their consumption from it, enabling flexibility for supporting various event types. *Event Registry* dynamically scans and imports Protocol Buffer `.proto` files located in the designated events folder. It creates a mapping between event types and their corresponding Protocol Buffer classes (`events_mapping`). This allows the system to handle multiple event types without hardcoding them. The `events_mapping` is used by consumers to deserialize events received from Kafka. Based on the `event_type` extracted from the Kafka message `key`, the corresponding Protocol Buffer class is fetched from the mapping and used to reconstruct the event in its original structured format.

**API**
The API exposes a `/store` endpoint that allows users to create and send events to Kafka. Each event includes a context and data payload, which are validated and serialized using `protobuf` before being sent to Kafka. As a part of the API, the Producer is responsible for generating and sending events to Kafka. Using the `ProducerKeyManager`, events are keyed to ensure partitioning consistency.

**Kafka Consumer** 
The consumer component subscribes to Kafka topics and processes incoming events. Events are deserialized and queued, then flushed to storage when specified thresholds (batch size or time interval) are met. This component ensures efficient handling and storage of high-throughput data. The `FileWriterBase` class provides a flexible interface allowing data to be stored in different backends based on configuration. `MinioFileWriter` class implements this base class.


## Installation
**Prerequisites:** 
* Python version 3.11
* Poetry version 1.8.3
* [Docker Desktop](https://docs.docker.com/desktop/) installed

**Setup steps**
* Clone the repository `git clone https://github.com/CarexNigra/event-collector.git`
* Navigate to the directory `cd event-collector`
* Install dependencies `make install`


## Configuration
There is a dev config file in `config/` folder: `dev.toml`. `stg.toml` and `prod.toml` may be added to this folder if needed. `dev.toml` provides configuration to run the application in docker. It consists of four sections:
* `general` defines general config for the application: 
    * `kafka_topic` to send events to / consume events from
    * `root_path` path to local folder where files with events will be saved 
    * `flush_interval` the interval (in seconds) for consumed message queue to be flushed to a new file
    * `max_output_file_size` file size (in bytes) not to be exceeded when flushing messages into a file
* `producer` defindes Kafka producer config. See the [reference](https://docs.confluent.io/platform/current/installation/configuration/producer-configs.html)
* `consumer` defindes Kafka consumer config. See the [reference](https://docs.confluent.io/platform/current/installation/configuration/consumer-configs.html)
* `minio` defines config for MinIO object storage except for credentials. 

Several environment variables need to be added (for being used in `docker-compose.yml`):
* Credentials for MinIO 
* `kafka_topic` matching the topic in `dev.toml` 
* `log_level` which defines what exactly will be logged. If you add `DEBUG`, DEBUG, INFO, WARNING and ERROR logging will be performed. If you add `INFO` - INFO, WARNING and ERROR only. If you add nothing, logging will cover just WARNING and ERROR.

It can be done as follows:
1. Open your .zshrc file (or other relevant shell configuration file) in terminal: `nano ~/.zshrc` 
2. Add MinIO credentials, kafka topic:
```
export MINIO_ACCESS_KEY="minio_user"
export MINIO_SECRET_KEY="minio_password"
export KAFKA_TOPIC="event-messages"
export LOG_LEVEL="INFO"
```
3. Save and exit: If you're using nano, press CTRL + X, then Y to confirm, and press Enter to save.
4. Apply the changes by sourcing the file or restarting your terminal `source ~/.zshrc`


## Usage
1. Run docker
    * Install docker desktop, if not yet installed, launch it
    * In terminal go to the folder with `docker-compose.yml` file (in our case ../local): `cd event_collector/local`
    * Run following command to create a container: `docker-compose up --build` (this builds and deploys api, consumer, 3 kafka brokers and minIO on docker)
    * In case of success you will see
```
init-kafka-1         | __consumer_offsets
init-kafka-1         | event-messages
init-kafka-1 exited with code 0
```
And then consumer app will start to print following logs (since no messages are yet sent) 
```
consumer-app         | {"level": "INFO", "timestamp": "2024-11-11T21:22:49.345842+00:00", "app": {"name": "event-collector", "releaseId": "undefined", "message": "(1) Consumption. Message: None", "extra": null}}
```

2. View consumed kafka messages in consumer logs
    * Open another terminal session
    * Run `docker ps`
    * In the output get docker `<container_id>` (first sting) with the service you are interested to check (e.g. local-consumer-app to test end-to-end)
    * stream logs for this service `docker logs -f <container_id>`

3. Send test request with an event to it
    * Open another terminal session
    * Send as many test events to api as you want (worth sending 10-15 to observe batching)
    ```shell
    curl -v -X POST -H "Content-Type: application/json" 'http://localhost:5000/store' -d '{"event_name": "TestEvent", "context": {"sent_at": 1701530942, "received_at": 1701530942, "processed_at": 1701530942, "message_id": "36eca638-4c0f-4d11-bc9b-cc2290851032", "user_agent": "some_user_agent"}, "data": {"user_id": "example_user_id", "account_id": "example_account_id", "user_role": "OWNER"}}'
    ```
    * You can also use another event type
    ```shell
    curl -v -X POST -H "Content-Type: application/json" 'http://localhost:5000/store' -d '{"event_name": "YetAnotherTestEvent", "context": {"sent_at": 1701530943, "received_at": 1701530944, "processed_at": 1701530945, "message_id": "36eca638-4c0f-4d11-bc9b-cc2290851555", "user_agent": "some_user_agent"}, "data": {"input_type": "MOVE", "object_id": "someObjectId1234", "object_type": "STICKY_NOTE"}}'
    ```

4. Check that event ends up in the consumer logs
    * In terminal with consumer container (and in Docker Dashboard UI) you will see consumed messages. Here is how it should look like
```
{"level": "INFO", "timestamp": "2024-11-11T21:15:35.344630+00:00", "app": {"name": "event-collector", "releaseId": "undefined", "message": "(1) Consumption. Message: <cimpl.Message object at 0xffff93a37c40>", "extra": null}}
{"level": "INFO", "timestamp": "2024-11-11T21:15:35.344995+00:00", "app": {"name": "event-collector", "releaseId": "undefined", "message": "(2) Parsing. Event class data type: <class 'dict'>, data: {'context': {'sentAt': '1701530942', 'receivedAt': '1701530942', 'processedAt': '1701530942', 'messageId': '36eca638-4c0f-4d11-bc9b-cc2290851032', 'userAgent': 'some_user_agent'}, 'userId': 'example_user_id', 'accountId': 'example_account_id', 'userRole': 'OWNER'}", "extra": null}}
{"level": "INFO", "timestamp": "2024-11-11T21:15:35.919841+00:00", "app": {"name": "event-collector", "releaseId": "undefined", "message": "(1) Consumption. Message: <cimpl.Message object at 0xffff93a37cc0>", "extra": null}}
{"level": "INFO", "timestamp": "2024-11-11T21:15:35.920253+00:00", "app": {"name": "event-collector", "releaseId": "undefined", "message": "(2) Parsing. Event class data type: <class 'dict'>, data: {'context': {'sentAt': '1701530942', 'receivedAt': '1701530942', 'processedAt': '1701530942', 'messageId': '36eca638-4c0f-4d11-bc9b-cc2290851032', 'userAgent': 'some_user_agent'}, 'userId': 'example_user_id', 'accountId': 'example_account_id', 'userRole': 'OWNER'}", "extra": null}}
{"level": "INFO", "timestamp": "2024-11-11T21:15:35.920336+00:00", "app": {"name": "event-collector", "releaseId": "undefined", "message": "(3) Flushing 32 parsed messages.", "extra": null}}
{"level": "INFO", "timestamp": "2024-11-11T21:15:35.925139+00:00", "app": {"name": "event-collector", "releaseId": "undefined", "message": "(4) Saving. JSON file saved to MinIO at: 2023/12/2/15/9670bd8f-2f53-4a01-8041-26662d563bec_1701530942.json", "extra": null}}
```

5. Check that events batch is written to a file in minIO
    * open minIO UI in your browser: `http://localhost:9001/login`
    * enter your credentials (the same you have as environment variables)
    * go to the `consumed_events` bucket, open all nested folders and verify that there is a newly created .json file there 
    * NOTE: If you want to see several files, consider sending events with different `received_at` values

## Testing
* Static + style checks, and tests: `make battery`
* Static checks `make static-check`
* Style checks `make style-check` and `make restyle`
* Tests `make tests`

## Next steps
Add Prometheus metrics
>>> TODO: Modify logs logic: log_level env var: to be able to set debug. Describe it here
