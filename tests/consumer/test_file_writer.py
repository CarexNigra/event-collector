import json
import os
import uuid

from consumer.file_writers import LocalFileWriter, MinioFileWriter, create_bucket, create_minio_client


def test_local_file_writing(batch_of_events_mock):  # , clean_up_temp):
    # (1) Define configs
    test_configs = {
        "save_to_path": "/tmp",
        "temp_folder_uuid": "consumer_test_" + str(uuid.uuid4()),
        "unique_consumer_id": "cons_gr_id_a4558670-396e-41d6-b596-110ebb6942c3",
    }
    # (2) Write file
    file_writer = LocalFileWriter(
        root_path=f"{test_configs['save_to_path']}/{test_configs['temp_folder_uuid']}",
    )
    file_writer.write_file(batch_of_events_mock, test_configs["unique_consumer_id"])

    # (3) Check that file has been written
    date_dict = file_writer.parse_received_at_date(batch_of_events_mock[0])
    folder_path = os.path.join(
        test_configs["save_to_path"],
        test_configs["temp_folder_uuid"],
        date_dict["year"],
        date_dict["month"],
        date_dict["day"],
        date_dict["hour"],
    )
    file_name = f"{test_configs['unique_consumer_id']}_{date_dict['int_timestamp']}.json"
    file_path = os.path.join(folder_path, file_name)
    assert os.path.exists(file_path)


def test_minio_writing(batch_of_events_mock, minio_mock):
    # (1) Define configs
    test_configs = {
        "save_to_path": "consumed-events",
        "unique_consumer_id": "cons_gr_id_a4558670-396e-41d6-b596-110ebb6942c3",
    }

    # (2) Instantiate minio file writer
    minio_config = {
        "endpoint": "localhost:9000",
        "access_key": "minio_user",
        "secret_key": "minio_password",
        "secure": False,
    }
    minio_client = create_minio_client(config=minio_config)
    create_bucket(test_configs["save_to_path"], minio_client)

    minio_file_writer = MinioFileWriter(
        root_path=test_configs["save_to_path"],
        minio_client=minio_client,
    )

    # (3) Write file
    minio_file_writer.write_file(batch_of_events_mock, test_configs["unique_consumer_id"])

    # (4) Check that file has been written
    date_dict = minio_file_writer.parse_received_at_date(batch_of_events_mock[0])
    folder_path = os.path.join(date_dict["year"], date_dict["month"], date_dict["day"], date_dict["hour"])
    file_name = f"{test_configs['unique_consumer_id']}_{date_dict['int_timestamp']}.json"
    file_path = os.path.join(folder_path, file_name)

    response = minio_file_writer._minio_client.get_object(test_configs["save_to_path"], file_path)
    written_data = response.read().decode("utf-8")
    response.close()
    response.release_conn()

    written_messages = [json.loads(line) for line in written_data.strip().split("\n")]
    assert len(written_messages) == len(batch_of_events_mock)
