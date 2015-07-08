import unittest
import wx
import re
import traceback
import sys
from os import path, listdir
from requests.exceptions import ConnectionError

from GUI.SettingsFrame import SettingsFrame


def dead_func(*args, **kwargs):
    """
    used to replace functions that don't need to be called
    """
    pass


class TestSettingsFrame(unittest.TestCase):

    def setUp(self):

        print "\nStarting " + self.__module__ + ": " + self._testMethodName
        self.app = wx.App(False)
        self.frame = SettingsFrame()
        self.frame.Show()

    def tearDown(self):

        self.frame.Destroy()
        self.app.Destroy()

    def test_valid_credentials(self):

        self.frame.create_api_obj = dead_func
        self.frame.attempt_connect_to_api()
        self.assertEqual(self.frame.base_URL_box.GetBackgroundColour(),
                         self.frame.VALID_CONNECTION_COLOR)

        self.assertIn("Successfully connected to API",
                      self.frame.log_panel.GetValue())

    def test_invalid_connection(self):

        def raise_connection_err():
            raise ConnectionError()

        self.frame.create_api_obj = raise_connection_err
        self.frame.attempt_connect_to_api()
        self.assertEqual(self.frame.base_URL_box.GetBackgroundColour(),
                         self.frame.INVALID_CONNECTION_COLOR)

        self.assertIn("Cannot connect to url",
                      self.frame.log_panel.GetValue())


def load_test_suite():

    gui_sf_test_suite = unittest.TestSuite()

    gui_sf_test_suite.addTest(
        TestSettingsFrame("test_valid_credentials"))
    gui_sf_test_suite.addTest(
        TestSettingsFrame("test_invalid_connection"))

    return gui_sf_test_suite


if __name__ == "__main__":

    sf_ts = load_test_suite()
    full_suite = unittest.TestSuite([sf_ts])

    runner = unittest.TextTestRunner()
    runner.run(full_suite)
