import unittest
from os import path

from API.directoryscanner import find_runs_in_directory

path_to_module = path.abspath(path.dirname(__file__))

class TestDirectoryScanner(unittest.TestCase):
    def test_single_end(self):
        runs = find_runs_in_directory(path.join(path_to_module, "single_end"))
        self.assertEqual(1, len(runs))
        self.assertEqual("SINGLE_END", runs[0].metadata["layoutType"])
        samples = runs[0].sample_list
        self.assertEqual(3, len(samples))

        for sample in samples:
            self.assertFalse(sample.is_paired_end())
