"""Module for parsing and validating config files."""
import sys
from json.decoder import (
        JSONDecoder,
        JSONDecodeError
        )

from src.logger import setup_logging

DECODER = JSONDecoder()
LOGGER = setup_logging()

def parse(config):
    """Parse the string of a config file."""
    try:
        output = DECODER.decode(config)
    except JSONDecodeError as err:
        LOGGER.error("Failed to parse config file: %s", err)
        raise
    except TypeError as err:
        LOGGER.error("Failed to parse config file: %s", err)
        raise

    return output
