"""A collection of utility functions"""
from datetime import datetime, timedelta


def read_file_content_into_list(file_path):
    """Read lines from a file, and remove speech marks (")."""
    if file_path is None:
        return None

    with open(file_path, encoding="UTF-8") as infile:
        list_of_content = [line.strip().replace('"', "") for line in infile]

    return list_of_content


def convert_list_of_key_value_pairs_to_dict(list_of_key_value_pairs):
    """Receive a list of strings, containing unparsed key-value pairs.
    Return a dictionary of parsed key-value pairs."""
    if not list_of_key_value_pairs:
        return {}

    return dict(x.split("=") for x in list_of_key_value_pairs)


def get_credentials_from_secret_file(file_path):
    """Return a dictionary of credentials from a file."""
    list_of_key_value_pairs = read_file_content_into_list(file_path)
    dict_of_credentials = convert_list_of_key_value_pairs_to_dict(
        list_of_key_value_pairs
    )
    return dict_of_credentials


def get_iso_timestamp_x_min_ago(minutes):
    """Return a timestamp of 'x' minutes ago, with microseconds set to 0."""
    timestamp = datetime.utcnow() - timedelta(minutes=minutes)
    return timestamp.replace(microsecond=0).isoformat()
