import unittest
# TODO: Move this code to a module so we don't depend on PYTHONPATH and that sort
# of ugliness.
from jarvis import convert_file_to_json

class TestJarvis(unittest.TestCase):

    def setUp(self):
        with open('fixtures/test_log.md', 'r') as f:
            self.test_log = f.read()

    def test_convert_log(self):
        try:
            j = convert_file_to_json(self.test_log)
            # Version 0.2.0
            expected_keys = sorted(['version', 'created', 'body', 'tags',
                'occurred', 'author'])
            actual_keys = sorted(j.keys())
            self.assertListEqual(expected_keys, actual_keys)
        except Exception as e:
            self.fail("Unexpected error while parsing test_log")


if __name__ == "__main__":
    unittest.main()
