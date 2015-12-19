import unittest
from collections import namedtuple
# TODO: Move this code to a module so we don't depend on PYTHONPATH and that sort
# of ugliness.
from jarvis import convert_file_to_json, get_tags

JarvisSettings = namedtuple('JarvisSettings', ['tags_directory'])

class TestJarvis(unittest.TestCase):

    def setUp(self):
        with open('fixtures/test_log.md', 'r') as f:
            self.test_log = f.read()

        self.js = JarvisSettings('fixtures/tags')

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

    def test_get_tags(self):
        expected_tags = ['TestA', 'TestB&C']
        actual_tags = get_tags(self.js)
        self.assertListEqual(expected_tags, actual_tags)


if __name__ == "__main__":
    """
    To run:
    export PYTHONPATH="$HOME/oz/workspace/Jarvis/bin"

    python -m unittest test_jarvis.py
    """
    unittest.main()
