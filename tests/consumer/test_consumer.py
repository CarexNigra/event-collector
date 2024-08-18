import os
import threading
import time
import uuid

# from consumer.consumer import LocalFileWriter, basic_consume_loop, get_config_path

from consumer.consumer import LocalFileWriter, EventConsumer, get_config_path

CONFIG_FILE_PATH = get_config_path()


# def test_consumption(event_mock, kafka_consumer_mock, clean_up_temp):
#     # (1) Mock config and define temp folder
#     general_config_dict = {
#         "kafka_topic": "event-messages",
#         "min_commit_count": 10,
#         "save_to_path": "/tmp",
#         "max_output_file_size": 1000,
#     }
#     temp_folder_uuid = "consumer_test_" + str(uuid.uuid4())

#     # (2) Run consume loop
#     # test_consumer.py runs in a main thread.
#     # We make basic_consume_loop to run in a separate thread to be able to end it
#     # when main testing thread ends (we define it as a daemon, so it is possible)
#     # Otherwise we enter into an infinite loop and test will never pass
#     consumer_thread = threading.Thread(
#         target=basic_consume_loop,
#         args=(
#             kafka_consumer_mock,
#             [general_config_dict["kafka_topic"]],
#             general_config_dict["min_commit_count"],
#             general_config_dict["save_to_path"] + f"/{temp_folder_uuid}",
#             general_config_dict["max_output_file_size"],
#         ),
#     )
#     consumer_thread.daemon = True
#     consumer_thread.start()
#     time.sleep(1.5)

#     # (3) Check that file has been created
#     message_dict = event_mock["event_json_data"]
#     file_writer = LocalFileWriter(
#         event_json_data=message_dict,
#         environment="dev",
#         root_path=general_config_dict["save_to_path"] + f"/{temp_folder_uuid}",
#         max_output_file_size=general_config_dict["max_output_file_size"],
#     )

#     full_file_path = file_writer.get_full_path()
#     print("full_file_path:", full_file_path)
#     assert os.path.exists(full_file_path)


def test_consumption(event_mock, kafka_consumer_mock, clean_up_temp):
    # (1) Mock config and define temp folder
    general_config_dict = {
        "kafka_topic": "event-messages",
        "min_commit_count": 10,
        "root_path": "/tmp",
        "max_output_file_size": 1000,
    }
    temp_folder_uuid = "consumer_test_" + str(uuid.uuid4())

    # (2) Instantiate file writer
    file_writer = LocalFileWriter(
        event_json_data={},
        root_path=general_config_dict["root_path"],
        max_output_file_size=general_config_dict["max_output_file_size"]
    )

    # (3) Instantiate event consumer
    event_consumer = EventConsumer(
        file_writer=file_writer,
        consumer=kafka_consumer_mock,
        topics=[general_config_dict["kafka_topic"]],
        min_commit_count=general_config_dict["min_commit_count"]
    )
    # TODO: Mock event consumer / file writer with _event_json_data?
    print("\n+++++ ", event_consumer._file_writer._event_json_data)

    # (2) Run consume loop
    # test_consumer.py runs in a main thread.
    # We make basic_consume_loop to run in a separate thread to be able to end it
    # when main testing thread ends (we define it as a daemon, so it is possible)
    # Otherwise we enter into an infinite loop and test will never pass
    consumer_thread = threading.Thread(
        target=event_consumer.run_consume_loop(),
    )
    consumer_thread.daemon = True
    consumer_thread.start()
    time.sleep(1.5)

    # (3) Check that file has been created
    message_dict = event_mock["event_json_data"]
    file_writer = LocalFileWriter(
        event_json_data=message_dict,
        root_path=general_config_dict["save_to_path"] + f"/{temp_folder_uuid}",
        max_output_file_size=general_config_dict["max_output_file_size"],
    )

    full_file_path = file_writer.get_full_path()
    print("full_file_path:", full_file_path)
    assert os.path.exists(full_file_path)