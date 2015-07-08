import unittest
import wx
import re
import traceback
import sys
from os import path, listdir
from requests.exceptions import ConnectionError
from collections import OrderedDict
import GUI.SettingsFrame
from mock import MagicMock, patch


POLL_INTERVAL = 100  # milliseconds
MAX_WAIT_TIME = 5000  # milliseconds


class Foo(object):

    """
    Class used to attach attributes
    """

    def __init__(self):
        pass


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


def assert_boxes_have_neutral_color(self):

    self.assertEqual(self.frame.base_URL_box.GetBackgroundColour(),
                     self.frame.NEUTRAL_BOX_COLOR)
    self.assertEqual(self.frame.username_box.GetBackgroundColour(),
                     self.frame.NEUTRAL_BOX_COLOR)
    self.assertEqual(self.frame.password_box.GetBackgroundColour(),
                     self.frame.NEUTRAL_BOX_COLOR)
    self.assertEqual(self.frame.client_id_box.GetBackgroundColour(),
                     self.frame.NEUTRAL_BOX_COLOR)
    self.assertEqual(self.frame.client_secret_box.GetBackgroundColour(),
                     self.frame.NEUTRAL_BOX_COLOR)


def poll_for_prompt_dlg(self, time_counter, handle_func):

    time_counter["value"] += POLL_INTERVAL

    if (self.frame.prompt_dlg is not None or
            time_counter["value"] == MAX_WAIT_TIME):
        self.frame.timer.Stop()

        try:
            handle_func(self)

        except (AssertionError, AttributeError):
            print traceback.format_exc()
            sys.exit(1)


def set_config_dict(self):

    self.frame.config_dict = OrderedDict()
    self.frame.config_dict["baseURL"] = "http://localhost:8080/api2"
    self.frame.config_dict["username"] = "admin2"
    self.frame.config_dict["password"] = "password2"
    self.frame.config_dict["client_id"] = "testClient2"
    self.frame.config_dict["client_secret"] = "testSecret2"


def set_boxes(self):

    self.frame.base_URL_box.SetValue(self.frame.config_dict["baseURL"])
    self.frame.username_box.SetValue(self.frame.config_dict["username"])
    self.frame.password_box.SetValue(self.frame.config_dict["password"])
    self.frame.client_id_box.SetValue(self.frame.config_dict["client_id"])
    self.frame.client_secret_box.SetValue(
        self.frame.config_dict["client_secret"])


class TestSettingsFrame(unittest.TestCase):

    @patch("GUI.SettingsFrame.RawConfigParser")
    def setUp(self, mock_confparser):

        """
        mock the built-in module RawConfigParser so that it doesn't actually
            read from the config file

        """

        print "\nStarting " + self.__module__ + ": " + self._testMethodName
        self.app = wx.App(False)

        foo = Foo()
        setattr(foo, "read", lambda f: None)
        setattr(foo, "get", lambda x, y: "")
        mock_confparser.side_effect = [foo]
        # RawConfigParser will now return foo when called
        # foo.read takes one argument "f" and returns None
        # foo.get takes two arguments "x", "y" and returns empty string
        # this gives a self.config_dict with None for all the keys
        # then we configure it with set_config_dict

        self.frame = GUI.SettingsFrame.SettingsFrame()
        set_config_dict(self)
        set_boxes(self)

        # self.frame.Show()

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
                         self.frame.NEUTRAL_BOX_COLOR)
        self.assertEqual(self.frame.password_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_BOX_COLOR)
        self.assertEqual(self.frame.client_id_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_BOX_COLOR)
        self.assertEqual(self.frame.client_secret_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_BOX_COLOR)

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
                         self.frame.NEUTRAL_BOX_COLOR)
        self.assertEqual(self.frame.client_id_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_BOX_COLOR)
        self.assertEqual(self.frame.client_secret_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_BOX_COLOR)

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
                         self.frame.NEUTRAL_BOX_COLOR)
        self.assertEqual(self.frame.username_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_BOX_COLOR)
        self.assertEqual(self.frame.password_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_BOX_COLOR)
        self.assertEqual(self.frame.client_secret_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_BOX_COLOR)

        self.assertIn("Invalid credentials",
                      self.frame.log_panel.GetValue())
        self.assertIn("Client ID is incorrect",
                      self.frame.log_panel.GetValue())

    def test_key_err_invalid_client_secret(self):

        def raise_key_err():
            raise KeyError("Bad client credentials")

        self.frame.create_api_obj = raise_key_err
        self.frame.attempt_connect_to_api()

        self.assertEqual(self.frame.client_secret_box.GetBackgroundColour(),
                         self.frame.INVALID_CONNECTION_COLOR)

        self.assertEqual(self.frame.base_URL_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_BOX_COLOR)
        self.assertEqual(self.frame.username_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_BOX_COLOR)
        self.assertEqual(self.frame.password_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_BOX_COLOR)
        self.assertEqual(self.frame.client_id_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_BOX_COLOR)

        self.assertIn("Invalid credentials",
                      self.frame.log_panel.GetValue())
        self.assertIn("Client Secret is incorrect",
                      self.frame.log_panel.GetValue())

    def test_value_err(self):

        def raise_val_err():
            raise ValueError()

        self.frame.create_api_obj = raise_val_err
        self.frame.attempt_connect_to_api()

        self.assertEqual(self.frame.base_URL_box.GetBackgroundColour(),
                         self.frame.INVALID_CONNECTION_COLOR)

        self.assertEqual(self.frame.client_secret_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_BOX_COLOR)
        self.assertEqual(self.frame.username_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_BOX_COLOR)
        self.assertEqual(self.frame.password_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_BOX_COLOR)
        self.assertEqual(self.frame.client_id_box.GetBackgroundColour(),
                         self.frame.NEUTRAL_BOX_COLOR)

        self.assertIn("Cannot connect to url",
                      self.frame.log_panel.GetValue())

    @patch("GUI.SettingsFrame.SettingsFrame.attempt_connect_to_api")
    @patch("GUI.SettingsFrame.SettingsFrame.write_config_data")
    @patch("GUI.SettingsFrame.SettingsFrame.load_curr_config")
    def test_restore_default_settings(self, mock_lcc, mock_wcd, mock_connect):

        expected_dict = {
            "username": GUI.SettingsFrame.DEFAULT_USERNAME,
            "client_secret": GUI.SettingsFrame.DEFAULT_CLIENT_SECRET,
            "password": GUI.SettingsFrame.DEFAULT_PASSWORD,
            "baseURL": GUI.SettingsFrame.DEFAULT_BASE_URL,
            "client_id": GUI.SettingsFrame.DEFAULT_CLIENT_ID
        }

        def _load_config(*args):
            self.frame.config_dict = OrderedDict(expected_dict)

        mock_lcc.side_effect = _load_config

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

        self.assertEqual(self.frame.base_URL_box.GetValue(), new_baseURL)
        self.assertEqual(self.frame.username_box.GetValue(), new_username)
        self.assertEqual(self.frame.password_box.GetValue(), new_password)
        self.assertEqual(self.frame.client_id_box.GetValue(), new_client_id)
        self.assertEqual(self.frame.client_secret_box.GetValue(),
                         new_client_secret)

        self.frame.log_panel.Clear()
        self.assertEqual(self.frame.log_panel.GetValue(), "")
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

        # boxes are white because we disable attempt_connect_to_api
        assert_boxes_have_neutral_color(self)

        self.assertIn("Settings restored to default values",
                      self.frame.log_panel.GetValue())
        self.assertIn("baseURL = " + GUI.SettingsFrame.DEFAULT_BASE_URL,
                      self.frame.log_panel.GetValue())
        self.assertIn("username = " + GUI.SettingsFrame.DEFAULT_USERNAME,
                      self.frame.log_panel.GetValue())
        self.assertIn("password = " + GUI.SettingsFrame.DEFAULT_PASSWORD,
                      self.frame.log_panel.GetValue())
        self.assertIn("client_id = " + GUI.SettingsFrame.DEFAULT_CLIENT_ID,
                      self.frame.log_panel.GetValue())
        self.assertIn("client_secret = " +
                      GUI.SettingsFrame.DEFAULT_CLIENT_SECRET,
                      self.frame.log_panel.GetValue())

    @patch("GUI.SettingsFrame.SettingsFrame.attempt_connect_to_api")
    @patch("GUI.SettingsFrame.SettingsFrame.write_config_data")
    @patch("GUI.SettingsFrame.SettingsFrame.load_curr_config")
    def test_save_settings(self, mock_lcc, mock_wcd, mock_connect_api):

        new_baseURL = "new_baseURL"
        new_username = "new_username"
        new_password = "new_password"
        new_client_id = "new_client_id"
        new_client_secret = "new_client_secret"

        expected_dict = {
            "username": new_username,
            "client_secret": new_client_secret,
            "password": new_password,
            "baseURL": new_baseURL,
            "client_id": new_client_id
        }

        def _load_config(*args):
            self.frame.config_dict = OrderedDict(expected_dict)

        mock_lcc.side_effect = _load_config

        self.frame.base_URL_box.SetValue(new_baseURL)
        self.frame.username_box.SetValue(new_username)
        self.frame.password_box.SetValue(new_password)
        self.frame.client_id_box.SetValue(new_client_id)
        self.frame.client_secret_box.SetValue(new_client_secret)

        self.assertEqual(self.frame.base_URL_box.GetValue(), new_baseURL)
        self.assertEqual(self.frame.username_box.GetValue(), new_username)
        self.assertEqual(self.frame.password_box.GetValue(), new_password)
        self.assertEqual(self.frame.client_id_box.GetValue(), new_client_id)
        self.assertEqual(self.frame.client_secret_box.GetValue(),
                         new_client_secret)

        push_button(self.frame.save_btn)
        assert_boxes_have_neutral_color(self)

        self.assertIn("Saving", self.frame.log_panel.GetValue())
        self.assertIn("baseURL = " + new_baseURL,
                      self.frame.log_panel.GetValue())
        self.assertIn("username = " + new_username,
                      self.frame.log_panel.GetValue())
        self.assertIn("password = " + new_password,
                      self.frame.log_panel.GetValue())
        self.assertIn("client_id = " + new_client_id,
                      self.frame.log_panel.GetValue())
        self.assertIn("client_secret = " + new_client_secret,
                      self.frame.log_panel.GetValue())

        expected_targ_section = "apiCalls"
        mock_wcd.assert_called_with(expected_targ_section, expected_dict)

    def test_save_settings_no_changes(self):

        self.frame.attempt_connect_to_api = dead_func

        self.frame.log_panel.Clear()
        self.assertEqual(self.frame.log_panel.GetValue(), "")
        push_button(self.frame.save_btn)

        assert_boxes_have_neutral_color(self)

        self.assertIn("No changes to save", self.frame.log_panel.GetValue())


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

    gui_sf_test_suite.addTest(
        TestSettingsFrame("test_value_err"))

    gui_sf_test_suite.addTest(
        TestSettingsFrame("test_restore_default_settings"))
    gui_sf_test_suite.addTest(
        TestSettingsFrame("test_save_settings"))

    gui_sf_test_suite.addTest(
        TestSettingsFrame("test_save_settings_no_changes"))

    # gui_sf_test_suite.addTest(
    #    TestSettingsFrame("test_close_with_unsaved_changes_save"))
    # gui_sf_test_suite.addTest(
    #    TestSettingsFrame("test_close_with_unsaved_changes_dont_save"))

    return gui_sf_test_suite


if __name__ == "__main__":

    sf_ts = load_test_suite()
    full_suite = unittest.TestSuite([sf_ts])

    runner = unittest.TextTestRunner()
    runner.run(full_suite)
