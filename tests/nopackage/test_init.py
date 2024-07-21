import os
import sys
import unittest

if __name__ == "__main__":
    TEST_MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
    TESTS_DIR = os.path.dirname(TEST_MODULE_DIR)
    REPO_DIR = os.path.dirname(TESTS_DIR)
    sys.path.insert(0, REPO_DIR)

from nopackage import (
    iconLinks,
    filename_from_url,
)


class TestNoPackage(unittest.TestCase):
    def test_icon_name_from_url(self):
        # Avoid saving ~/.local/share/pixmaps/boscaceoil.blue.png?raw=true:
        self.assertEqual(filename_from_url("https://github.com/YuriSizov/boscaceoil-blue/blob/main/icon.png?raw=true"), "icon.png")
        self.assertEqual(filename_from_url("https://github.com/JustOff/Basilisk/blob/master/basilisk/branding/official/default48.png?raw=true"), "default48.png")


if __name__ == "__main__":
    unittest.main()