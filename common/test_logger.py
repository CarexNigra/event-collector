
from logger import get_logger

# Use the logger
logger = get_logger()

if __name__ == "__main__":
    # Example log statements
    logger.debug("This is a DEBUG log")
    logger.info("This is an INFO log")
    logger.warning("This is a WARNING log")
    logger.error("This is a ERROR log")