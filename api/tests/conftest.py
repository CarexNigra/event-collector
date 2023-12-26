from unittest.mock import patch, MagicMock
import pytest

# @pytest.fixture
# def kafka_producer_mock():
#     # Mock the Kafka producer
#     with patch("api.app.create_kafka_producer") as create_kafka_producer_mock:
#         producer_mock = MagicMock()
#         producer_mock.produce = MagicMock()
#         create_kafka_producer_mock.return_value = producer_mock
#         yield producer_mock


@pytest.fixture
def kafka_producer_mock():
    with patch("api.app.Producer") as kafka_producer_mock:
        kafka_producer_mock = MagicMock()
        kafka_producer_mock.produce = MagicMock()
        yield kafka_producer_mock



# @fixture(scope="session")
# def triton_mock():
#     with patch("api.model.grpc.InferenceServerClient") as m:
#         triton_client_grpc = MagicMock()
#         infer_result = MagicMock()
#         infer_result.as_numpy.return_value = np.array([b"42"])
#         triton_client_grpc.infer.return_value = infer_result
#         m.return_value = triton_client_grpc
#         yield