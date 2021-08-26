"""Test that the config parsing module is operating as expected."""
import unittest

from json.decoder import JSONDecodeError
from collectington.config import parse, validate


class TestConfigParse(unittest.TestCase):
    """Test that the config parsing function is operating as expected."""

    def test_parse_valid_json(self):
        """Test that function parses json correctly."""
        test_json = '{"json": "test", "one": 1}'
        expected = {"json": "test", "one": 1}

        output = parse(test_json)

        self.assertEqual(output, expected)

    def test_parse_fails_with_invalid_json(self):
        """Ensure the correct Error is thrown if input isn't valid json."""
        test_string = "invalid json"

        with self.assertRaises(JSONDecodeError):
            parse(test_string)

    def test_parse_fails_with_non_string_input(self):
        """Ensure that a TypeError is thrown if a string isn't provided as an argument."""
        test_input = 3

        with self.assertRaises(TypeError):
            parse(test_input)


class TestConfigValidateConfig(unittest.TestCase):
    """Test that configs are validated correctly."""

    def test_parse_valid_config(self):
        """Test that a valid config will not raise any exceptions."""
        with open(
            "collectington/test/files/config/config.json", encoding="utf-8"
        ) as file:
            valid_config = file.read()

        parsed_config = parse(valid_config)

        try:
            validate(parsed_config)
        except ValueError as err:
            self.fail(f"Exception raised:\n{err}")


if __name__ == "__main__":
    unittest.main()
