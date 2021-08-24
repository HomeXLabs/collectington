import unittest

from src.config import parse
from json.decoder import JSONDecodeError

class TestConfig(unittest.TestCase):
    def test_parse_valid_json(self):
        test_json = '{"json": "test", "one": 1}'
        expected = {
                "json": "test",
                "one": 1
                }

        output = parse(test_json)

        self.assertEqual(output, expected)

    def test_parse_fails_with_invalid_json(self):
        test_string = 'invalid json'

        with self.assertRaises(JSONDecodeError):
            parse(test_string)

    def test_parse_fails_with_non_string_input(self):
        test_input = 3

        with self.assertRaises(TypeError):
            parse(test_input)

if __name__ == '__main__':
    unittest.main()
