"""A collection of utility functions"""
from datetime import datetime, timedelta

import hvac


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


def get_latency_seconds(from_time: datetime, now: datetime = None) -> int:
    """Method to compare a UTC datetime with current time for latency metrics."""
    if not now:
        now = datetime.utcnow()

    latency = now - from_time
    return latency.total_seconds()


def login_to_vault_approle(vault_address, vault_role_id, vault_secret_id):
    """Use Vault to authenticate using a specified Approle."""
    vault = hvac.Client(url=vault_address)
    vault.auth.approle.login(
        role_id=vault_role_id,
        secret_id=vault_secret_id,
    )
    return vault


def read_secret(vault, secret_path, secret_engine=None) -> dict:
    """Extract the specific data from secret_path.

    Each secret_engine has its own response format. We currently support
    returning just the data for key_value_v2 and database engines.

    The response structure can be determined from the "Sample Response" of the
    appropriate read command from https://www.vaultproject.io/api-docs/secret.
    """
    secret_response = vault.read(secret_path)

    if secret_engine == "database":
        secret = secret_response.get("data")
    elif secret_engine == "kv_version_2":
        secret = secret_response.get("data").get("data")
    else:
        secret = secret_response

    return secret
