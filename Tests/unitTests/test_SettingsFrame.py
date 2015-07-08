import unittest
import wx
import re
import traceback
import sys
from os import path, listdir
from requests.exceptions import ConnectionError

import GUI.SettingsFrame


def push_button(targ_obj):
    """
    helper function that sends the event wx.EVT_BUTTON to the given targ_obj
    """
    button_evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, targ_obj.GetId())
    targ_obj.GetEventHandler().ProcessEvent(button_evt)

def dead_func(*args, **kwargs):
    """
    used to replace functions that don't need to be called
    """
    pass


class TestSettingsFrame(unittest.TestCase):

    def setUp(self):

        print "\nStarting " + self.__module__ + ": " + self._testMethodName
        self.app = wx.App(False)
        self.frame = GUI.SettingsFrame.SettingsFrame()
        self.frame.Show()

    def tearDown(self):

        self.frame.Destroy()
        self.app.Destroy()

    def test_valid_credentials(self):

        self.frame.create_api_obj = dead_func
        self.frame.attempt_connect_to_api()

        self.assertEqual(self.frame.base_URL_box.GetBackgroundColour(),
                         self.frame.VALID_CONNECTION_COLOR)
        self.assertEqual(self.frame.username_box.GetBackgroundColour(),
                         self.frame.VALID_CONNECTION_COLOR)
        self.assertEqual(self.frame.password_box.GetBackgroundColour(),
                         self.frame.VALID_CONNECTION_COLOR)
        self.assertEqual(self.frame.client_id_box.GetBackgroundColour(),
                         self.frame.VALID_CONNECTION_COLOR)
        self.assertEqual(self.frame.client_secret_box.GetBackgroundColour(),
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

        self.assertEqual(self.frame.username_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_TXT_CTRL_COLOR)
        self.assertEqual(self.frame.password_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_TXT_CTRL_COLOR)
        self.assertEqual(self.frame.client_id_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_TXT_CTRL_COLOR)
        self.assertEqual(self.frame.client_secret_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_TXT_CTRL_COLOR)

        self.assertIn("Cannot connect to url",
                      self.frame.log_panel.GetValue())

    def test_key_err_invalid_user_or_pass(self):

        def raise_key_err():
            raise KeyError("Bad credentials")

        self.frame.create_api_obj = raise_key_err
        self.frame.attempt_connect_to_api()

        self.assertEqual(self.frame.username_box.GetBackgroundColour(),
                         self.frame.INVALID_CONNECTION_COLOR)
        self.assertEqual(self.frame.password_box.GetBackgroundColour(),
                         self.frame.INVALID_CONNECTION_COLOR)

        self.assertEqual(self.frame.base_URL_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_TXT_CTRL_COLOR)
        self.assertEqual(self.frame.client_id_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_TXT_CTRL_COLOR)
        self.assertEqual(self.frame.client_secret_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_TXT_CTRL_COLOR)

        self.assertIn("Invalid credentials",
                      self.frame.log_panel.GetValue())
        self.assertIn("Username or password is incorrect",
                      self.frame.log_panel.GetValue())

    def test_key_err_invalid_client_id(self):

        def raise_key_err():
            raise KeyError("clientId does not exist")

        self.frame.create_api_obj = raise_key_err
        self.frame.attempt_connect_to_api()

        self.assertEqual(self.frame.client_id_box.GetBackgroundColour(),
                         self.frame.INVALID_CONNECTION_COLOR)

        self.assertEqual(self.frame.base_URL_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_TXT_CTRL_COLOR)
        self.assertEqual(self.frame.username_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_TXT_CTRL_COLOR)
        self.assertEqual(self.frame.password_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_TXT_CTRL_COLOR)
        self.assertEqual(self.frame.client_secret_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_TXT_CTRL_COLOR)

        self.assertIn("Invalid credentials",
                      self.frame.log_panel.GetValue())

    def test_key_err_invalid_client_secret(self):

        def raise_key_err():
            raise KeyError("Bad client credentials")

        self.frame.create_api_obj = raise_key_err
        self.frame.attempt_connect_to_api()

        self.assertEqual(self.frame.client_secret_box.GetBackgroundColour(),
                         self.frame.INVALID_CONNECTION_COLOR)

        self.assertEqual(self.frame.base_URL_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_TXT_CTRL_COLOR)
        self.assertEqual(self.frame.username_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_TXT_CTRL_COLOR)
        self.assertEqual(self.frame.password_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_TXT_CTRL_COLOR)
        self.assertEqual(self.frame.client_id_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_TXT_CTRL_COLOR)

        self.assertIn("Invalid credentials",
                      self.frame.log_panel.GetValue())

    def test_restore_default_settings(self):

        self.frame.write_config_data = dead_func

        new_baseURL = "new_baseURL"
        new_username = "new_username"
        new_password = "new_password"
        new_client_id = "new_client_id"
        new_client_secret = "new_client_secret"

        self.frame.base_URL_box.SetValue(new_baseURL)
        self.frame.username_box.SetValue(new_username)
        self.frame.password_box.SetValue(new_password)
        self.frame.client_id_box.SetValue(new_client_id)
        self.frame.client_secret_box.SetValue(new_client_secret)

        self.assertEqual(self.frame.base_URL_box.GetValue(),
                                 new_baseURL)
        self.assertEqual(self.frame.username_box.GetValue(),
                                 new_username)
        self.assertEqual(self.frame.password_box.GetValue(),
                                 new_password)
        self.assertEqual(self.frame.client_id_box.GetValue(),
                                 new_client_id)
        self.assertEqual(self.frame.client_secret_box.GetValue(),
                                 new_client_secret)

        push_button(self.frame.default_btn)

        self.assertEqual(self.frame.base_URL_box.GetValue(),
                                 GUI.SettingsFrame.DEFAULT_BASE_URL)
        self.assertEqual(self.frame.username_box.GetValue(),
                                 GUI.SettingsFrame.DEFAULT_USERNAME)
        self.assertEqual(self.frame.password_box.GetValue(),
                                 GUI.SettingsFrame.DEFAULT_PASSWORD)
        self.assertEqual(self.frame.client_id_box.GetValue(),
                                 GUI.SettingsFrame.DEFAULT_CLIENT_ID)
        self.assertEqual(self.frame.client_secret_box.GetValue(),
                                 GUI.SettingsFrame.DEFAULT_CLIENT_SECRET)

        self.assertEqual(self.frame.base_URL_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_TXT_CTRL_COLOR)
        self.assertEqual(self.frame.username_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_TXT_CTRL_COLOR)
        self.assertEqual(self.frame.password_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_TXT_CTRL_COLOR)
        self.assertEqual(self.frame.client_id_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_TXT_CTRL_COLOR)
        self.assertEqual(self.frame.client_secret_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_TXT_CTRL_COLOR)

        self.assertIn("Settings restored to default values",
                      self.frame.log_panel.GetValue())


def load_test_suite():

    gui_sf_test_suite = unittest.TestSuite()

    gui_sf_test_suite.addTest(
        TestSettingsFrame("test_valid_credentials"))
    gui_sf_test_suite.addTest(
        TestSettingsFrame("test_invalid_connection"))
    gui_sf_test_suite.addTest(
        TestSettingsFrame("test_key_err_invalid_user_or_pass"))
    gui_sf_test_suite.addTest(
        TestSettingsFrame("test_key_err_invalid_client_id"))
    gui_sf_test_suite.addTest(
        TestSettingsFrame("test_key_err_invalid_client_secret"))
    # test ValueError

    gui_sf_test_suite.addTest(
        TestSettingsFrame("test_restore_default_settings"))

    return gui_sf_test_suite


if __name__ == "__main__":

    sf_ts = load_test_suite()
    full_suite = unittest.TestSuite([sf_ts])

    runner = unittest.TextTestRunner()
    runner.run(full_suite)
