import importlib
import inspect
import os

from common.logger import get_logger

logger = get_logger()

FOLDER_PATH = "events"  
# NOTE: can keep it here for now, since events folder doesn't change, and sticks to this repo structure


def get_pb2_files_names(folder_path):
    pb2_file_names = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith("_pb2.pyi"):
                pb2_file_names.append(os.path.join(root, file[:-4]))
    return pb2_file_names


def get_events_mapping(folder_path):
    pb2_files_names_list = get_pb2_files_names(folder_path)
    events_mapping = {}

    for file_name in pb2_files_names_list:
        module_name = file_name.replace("/", ".")
        try:
            imported_module = importlib.import_module(module_name)
            d = {k: v for k, v in imported_module.__dict__.items() if not k.startswith("_") and inspect.isclass(v)}

            for k in d:
                events_mapping[d[k].__name__] = d[k]
                logger.info(d[k].DESCRIPTOR.GetOptions())

        except ImportError as e:
            logger.info(f"Error importing module {module_name}: {e}")

    return events_mapping


events_mapping = get_events_mapping(FOLDER_PATH)


# if __name__ == "__main__":
#     print("Events mapping:", events_mapping)
