import datetime
import mock
import unittest

import hvac

from collectington.utils import get_latency_seconds, read_file_content_into_list, read_secret
from test import MOCK_DATA_DIR


class TestUtils(unittest.TestCase):
    def test_read_file_content_into_list(self):
        mock_file = f"{MOCK_DATA_DIR}/mock_read_file_content_into_list"

        expected_content = ["CONTENT_1=test", "CONTENT_2=123"]
        content = read_file_content_into_list(mock_file)

        self.assertEqual(expected_content, content)

    def test_calc_latency_seconds(self):
        mock_time = datetime.datetime(2021, 1, 1, 23, 59, 0)
        mock_now = datetime.datetime(2021, 1, 2, 0, 0, 0)
        result = get_latency_seconds(mock_time, mock_now)
        self.assertEqual(result, 60)

    @mock.patch.object(hvac, "Client")
    def test_read_secret(self, mock_vault):
        mock_vault.read.return_value = {"data": {"password": 123}}
        secret = read_secret(mock_vault, "mock/path", secret_engine="database")
        self.assertEqual(secret["password"], 123)

        mock_vault.read.return_value = {"data": {"data": {"secret_id": 123}}}
        secret = read_secret(mock_vault, "mock/path", secret_engine="kv_version_2")
        self.assertEqual(secret["secret_id"], 123)
