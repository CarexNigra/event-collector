import glob
import math
import os
import uuid
import json

from consumer.consumer import LocalFileWriter, MinioFileWriter, create_bucket, create_minio_client
from pytest_minio_mock.plugin import minio_mock


def test_local_file_writing(event_mock, clean_up_temp):
    test_configs = {
        "save_to_path": "/tmp",
        "temp_folder_uuid": "consumer_test_" + str(uuid.uuid4()),
        "max_output_file_size": 1000,
        "number_of_test_messages": 10,
    }

    total_message_size = 0

    for i in range(test_configs["number_of_test_messages"]):
        message_dict = event_mock()["event_json_data"]
        # Modify message for it to be potentially written into the next file
        message_dict["context"]["receivedAt"] = str(int(message_dict["context"]["receivedAt"]) + i)

        file_writer = LocalFileWriter(
            event_json_data=message_dict,
            root_path=f"{test_configs['save_to_path']}/{test_configs['temp_folder_uuid']}",
            max_output_file_size=test_configs["max_output_file_size"],
        )
        file_writer.write_file()

        # Update iterator (1 test message size is 266 bytes)
        total_message_size += 266

        # Get last file path (it is impossible to use get_full_path directly,
        # issues when the last file size exeeds the max_output_file_size threshold)
        date_dict = file_writer.parse_received_at_date()
        folder_path = os.path.join(
            test_configs["save_to_path"],
            test_configs["temp_folder_uuid"],
            date_dict["year"],
            date_dict["month"],
            date_dict["day"],
            date_dict["hour"],
        )

        json_files = glob.glob(os.path.join(folder_path, "*.json"))
        most_recent_file_path = max(json_files, key=lambda f: int(os.path.splitext(os.path.basename(f))[0]))
        assert os.path.exists(most_recent_file_path)

    number_of_files_calculated = math.ceil(total_message_size / test_configs["max_output_file_size"])
    number_of_files_actual = len(json_files)
    assert number_of_files_calculated == number_of_files_actual



def test_minio_writing(event_mock, minio_mock):
    # (1) Define configs
    test_configs = {
        "save_to_path": "consumed-events",
        "max_output_file_size": 1000,
    }
    # (2) Instantiate minio file writer
    minio_client = create_minio_client()
    create_bucket(test_configs["save_to_path"], minio_client)
    message_dict = event_mock()["event_json_data"]

    minio_file_writer = MinioFileWriter(
            event_json_data=message_dict,
            root_path=test_configs["save_to_path"],
            minio_client=minio_client,
            max_output_file_size=test_configs["max_output_file_size"]
        )
    
    # (3) Write file
    minio_file_writer.write_file()

    # (4) Get path to the writing dir
    date_dict = minio_file_writer.parse_received_at_date()
    folder_path = os.path.join(date_dict["year"], date_dict["month"], date_dict["day"], date_dict["hour"])
    
    # (5) Get all json files in the dir
    objects = minio_file_writer._minio_client.list_objects(test_configs['save_to_path'], prefix=folder_path, recursive=False)
    json_files = [obj.object_name for obj in objects if obj.object_name.endswith('.json')]

    most_recent_file_path = max(json_files, key=lambda f: int(os.path.splitext(os.path.basename(f))[0]))

    response = minio_file_writer._minio_client.get_object(test_configs['save_to_path'], most_recent_file_path)
    existing_data = json.load(response)
    response.close()
    response.release_conn()

    assert len(existing_data) != 0

    

