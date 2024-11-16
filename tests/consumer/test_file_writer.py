import json
import os

from pytest_minio_mock.plugin import minio_mock  # type: ignore  # noqa: F401

from consumer.file_writers.base import get_list_hash
from consumer.file_writers.minio import MinioFileWriter, create_minio_client
from config.config import MinioProperties


def test_minio_writing(batch_of_events_mock, minio_mock):  # noqa: F811
    # (1) Define configs
    test_configs = {
        "save_to_path": "consumed-events",
        "unique_consumer_id": "cons_gr_id_a4558670-396e-41d6-b596-110ebb6942c3",
    }

    # (2) Instantiate minio file writer
    minio_config = MinioProperties(
        endpoint="localhost:9000",
        access_key="minio_user",
        secret_key="minio_password",
        secure=False,
    )
    minio_client = create_minio_client(minio_config=minio_config)

    minio_file_writer = MinioFileWriter(
        root_path=test_configs["save_to_path"],
        minio_client=minio_client,
    )
    minio_file_writer.create_bucket()

    # (3) Write file
    minio_file_writer.write_file(batch_of_events_mock, test_configs["unique_consumer_id"])

    # (4) Check that file has been written
    date_dict = minio_file_writer.parse_received_at_date(batch_of_events_mock[0])
    folder_path = os.path.join(date_dict["year"], date_dict["month"], date_dict["day"], date_dict["hour"])
    batch_hash = get_list_hash(batch_of_events_mock)
    file_name = f"{test_configs['unique_consumer_id']}_{batch_hash}.json"
    file_path = os.path.join(folder_path, file_name)

    response = minio_file_writer._minio_client.get_object(test_configs["save_to_path"], file_path)
    written_data = response.read().decode("utf-8")
    response.close()
    response.release_conn()

    written_messages = [json.loads(line) for line in written_data.strip().split("\n")]
    assert len(written_messages) == len(batch_of_events_mock)
