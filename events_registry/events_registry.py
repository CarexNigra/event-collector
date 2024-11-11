import importlib
import inspect
import os

from common.logger import get_logger

logger = get_logger()

FOLDER_PATH = "events"
# NOTE: can keep it here, since events folder doesn't change, and sticks to this repo structure


def get_pb2_files_names(folder_path: str) -> list[str]:
    """
    Retrieves the names of protocol buffer (`_pb2.pyi`) files within a given folder path.

    Args:
        folder_path (str): The path to the folder containing protocol buffer files.
    Returns:
        list[str]: A list of protocol buffer file names (without extensions) found in the specified folder path.
    """
    pb2_file_names = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith("_pb2.pyi"):
                pb2_file_names.append(os.path.join(root, file[:-4]))
    return pb2_file_names


def get_events_mapping(folder_path: str) -> dict[str, type]:
    """
    Creates a mapping of event classes by importing classes from protocol buffer files
    within a specified folder path.

    Args:
        folder_path (str): The path to the folder containing protocol buffer files.
    Returns:
        dict[str, type]: A dictionary where keys are class names (as strings) and values
                         are class types imported from the protocol buffer modules.
    Raises:
        An import error message if a module fails to import.
    """
    pb2_files_names_list = get_pb2_files_names(folder_path)
    events_mapping = {}

    for file_name in pb2_files_names_list:
        module_name = file_name.replace("/", ".")
        try:
            imported_module = importlib.import_module(module_name)
            d = {k: v for k, v in imported_module.__dict__.items() if not k.startswith("_") and inspect.isclass(v)}

            for k in d:
                events_mapping[d[k].__name__] = d[k]
        except ImportError as e:
            logger.info(f"Error importing module {module_name}: {e}")

    return events_mapping


events_mapping = get_events_mapping(FOLDER_PATH)
