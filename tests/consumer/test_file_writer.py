import glob
import math
import os
import uuid

from consumer.consumer import LocalFileWriter


def test_file_writing(event_mock, clean_up_temp):
    test_configs = {
        "save_to_path": "/tmp",
        "temp_folder_uuid": "consumer_test_" + str(uuid.uuid4()),
        "max_output_file_size": 1000,
        "number_of_test_messages": 10,
    }

    total_message_size = 0

    for i in range(test_configs["number_of_test_messages"]):
        message_dict = event_mock["event_json_data"]
        # Modify message for it to be potentially written into the next file
        message_dict["context"]["receivedAt"] = str(int(message_dict["context"]["receivedAt"]) + i)

        file_writer = LocalFileWriter(
            event_json_data=message_dict,
            environment="dev",
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
        assert os.path.exists(most_recent_file_path) == True

    number_of_files_calculated = math.ceil(total_message_size / test_configs["max_output_file_size"])
    number_of_files_actual = len(json_files)
    assert number_of_files_calculated == number_of_files_actual
