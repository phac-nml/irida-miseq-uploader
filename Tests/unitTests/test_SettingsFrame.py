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


def click_checkbox(targ_obj):

    """
    helper function that sends the event wx.EVT_CHECKBOX to the given targ_obj
    """

    targ_obj.SetValue(True)
    checkbox_evt = wx.PyCommandEvent(wx.EVT_CHECKBOX.typeId,
                                     targ_obj.GetId())
    targ_obj.GetEventHandler().ProcessEvent(checkbox_evt)


def push_button(targ_obj):

    """
    helper function that sends the event wx.EVT_BUTTON to the given targ_obj
    """

    button_evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, targ_obj.GetId())
    targ_obj.GetEventHandler().ProcessEvent(button_evt)


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


class TestSettingsFrame(unittest.TestCase):

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
        # this gives a self.config_dict with empty string for all the keys
        # then we configure it with set_config_dict & update boxes w/ set_boxes

        self.frame = GUI.SettingsFrame.SettingsFrame()
        self.set_config_dict()
        self.set_boxes()

        # self.frame.Show()

    def tearDown(self):

        self.frame.Destroy()
        self.app.Destroy()

    @patch("GUI.SettingsFrame.ApiCalls")
    def test_valid_credentials(self, mock_apicalls):

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

        self.assertEqual(self.frame.base_URL_icon.Label, "success")
        self.assertEqual(self.frame.username_icon.Label, "success")
        self.assertEqual(self.frame.password_icon.Label, "success")
        self.assertEqual(self.frame.client_id_icon.Label, "success")
        self.assertEqual(self.frame.client_secret_icon.Label, "success")

    @patch("GUI.SettingsFrame.ApiCalls")
    def test_invalid_connection(self, mock_apicalls):

        mock_apicalls.side_effect = [ConnectionError()]
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
        self.assertNotIn("Message from server",
                         self.frame.log_panel.GetValue())

        self.assertEqual(self.frame.base_URL_icon.Label, "warning")
        self.assertEqual(self.frame.username_icon.Label, "hidden")
        self.assertEqual(self.frame.password_icon.Label, "hidden")
        self.assertEqual(self.frame.client_id_icon.Label, "hidden")
        self.assertEqual(self.frame.client_secret_icon.Label, "hidden")

    @patch("GUI.SettingsFrame.ApiCalls")
    def test_key_err_invalid_user_or_pass(self, mock_apicalls):

        mock_apicalls.side_effect = [KeyError("Bad credentials")]
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
        self.assertIn("Username and/or password is incorrect",
                      self.frame.log_panel.GetValue())
        self.assertNotIn("Message from server",
                         self.frame.log_panel.GetValue())

        self.assertEqual(self.frame.base_URL_icon.Label, "hidden")
        self.assertEqual(self.frame.username_icon.Label, "warning")
        self.assertEqual(self.frame.password_icon.Label, "warning")
        self.assertEqual(self.frame.client_id_icon.Label, "hidden")
        self.assertEqual(self.frame.client_secret_icon.Label, "hidden")

    @patch("GUI.SettingsFrame.ApiCalls")
    def test_key_err_invalid_client_id(self, mock_apicalls):

        mock_apicalls.side_effect = [KeyError("clientId does not exist")]
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
        self.assertNotIn("Message from server",
                         self.frame.log_panel.GetValue())

        self.assertEqual(self.frame.base_URL_icon.Label, "hidden")
        self.assertEqual(self.frame.username_icon.Label, "hidden")
        self.assertEqual(self.frame.password_icon.Label, "hidden")
        self.assertEqual(self.frame.client_id_icon.Label, "warning")
        self.assertEqual(self.frame.client_secret_icon.Label, "hidden")

    @patch("GUI.SettingsFrame.ApiCalls")
    def test_key_err_invalid_client_secret(self, mock_apicalls):

        mock_apicalls.side_effect = [KeyError("Bad client credentials")]
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
        self.assertNotIn("Message from server",
                         self.frame.log_panel.GetValue())

        self.assertEqual(self.frame.base_URL_icon.Label, "hidden")
        self.assertEqual(self.frame.username_icon.Label, "hidden")
        self.assertEqual(self.frame.password_icon.Label, "hidden")
        self.assertEqual(self.frame.client_id_icon.Label, "hidden")
        self.assertEqual(self.frame.client_secret_icon.Label, "warning")

    @patch("GUI.SettingsFrame.ApiCalls")
    def test_value_err(self, mock_apicalls):

        mock_apicalls.side_effect = [ValueError()]
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
        self.assertNotIn("Message from server",
                         self.frame.log_panel.GetValue())

        self.assertEqual(self.frame.base_URL_icon.Label, "warning")
        self.assertEqual(self.frame.username_icon.Label, "hidden")
        self.assertEqual(self.frame.password_icon.Label, "hidden")
        self.assertEqual(self.frame.client_id_icon.Label, "hidden")
        self.assertEqual(self.frame.client_secret_icon.Label, "hidden")

    @patch("GUI.SettingsFrame.ApiCalls")
    def test_unexpected_err(self, mock_apicalls):

        mock_apicalls.side_effect = [SyntaxError()]
        self.frame.attempt_connect_to_api()

        assert_boxes_have_neutral_color(self)

        self.assertIn("Unexpected error",
                      self.frame.log_panel.GetValue())

        self.assertEqual(self.frame.base_URL_icon.Label, "hidden")
        self.assertEqual(self.frame.username_icon.Label, "hidden")
        self.assertEqual(self.frame.password_icon.Label, "hidden")
        self.assertEqual(self.frame.client_id_icon.Label, "hidden")
        self.assertEqual(self.frame.client_secret_icon.Label, "hidden")

    @patch("GUI.SettingsFrame.SettingsFrame.attempt_connect_to_api")
    @patch("GUI.SettingsFrame.SettingsFrame.write_config_data")
    @patch("GUI.SettingsFrame.SettingsFrame.load_curr_config")
    def test_restore_default_settings(self, mock_lcc, mock_wcd,
                                      mock_connect_api):

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

        # assert box values update to show default settings
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

        self.assertIn("Settings restored to default values",
                      self.frame.log_panel.GetValue())
        self.assertIn("baseURL = " + GUI.SettingsFrame.DEFAULT_BASE_URL,
                      self.frame.log_panel.GetValue())
        self.assertIn("username = " + GUI.SettingsFrame.DEFAULT_USERNAME,
                      self.frame.log_panel.GetValue())
        self.assertIn("password = " +
                      len(GUI.SettingsFrame.DEFAULT_PASSWORD) * "*",
                      self.frame.log_panel.GetValue())
        self.assertIn("client_id = " + GUI.SettingsFrame.DEFAULT_CLIENT_ID,
                      self.frame.log_panel.GetValue())
        self.assertIn("client_secret = " +
                      GUI.SettingsFrame.DEFAULT_CLIENT_SECRET,
                      self.frame.log_panel.GetValue())

        # boxes are white because we mock attempt_connect_to_api
        assert_boxes_have_neutral_color(self)

        self.assertTrue(mock_lcc.called)
        self.assertTrue(mock_connect_api.called)

        expected_targ_section = "apiCalls"
        mock_wcd.assert_called_with(expected_targ_section, expected_dict)

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

        # assert box values remain the same after clicking save
        self.assertEqual(self.frame.base_URL_box.GetValue(), new_baseURL)
        self.assertEqual(self.frame.username_box.GetValue(), new_username)
        self.assertEqual(self.frame.password_box.GetValue(), new_password)
        self.assertEqual(self.frame.client_id_box.GetValue(), new_client_id)
        self.assertEqual(self.frame.client_secret_box.GetValue(),
                         new_client_secret)

        self.assertIn("Saving", self.frame.log_panel.GetValue())
        self.assertIn("baseURL = " + new_baseURL,
                      self.frame.log_panel.GetValue())
        self.assertIn("username = " + new_username,
                      self.frame.log_panel.GetValue())
        self.assertIn("password = " + len(new_password) * "*",
                      self.frame.log_panel.GetValue())
        self.assertIn("client_id = " + new_client_id,
                      self.frame.log_panel.GetValue())
        self.assertIn("client_secret = " + new_client_secret,
                      self.frame.log_panel.GetValue())

        # assert that previous info on log panel was cleared
        expected_num_lines = len(self.frame.config_dict.keys()) + 3
        # 1 line for "Saving"
        # 2 lines for "\n" at end of message
        self.assertEqual(self.frame.log_panel.GetNumberOfLines(),
                         expected_num_lines)

        assert_boxes_have_neutral_color(self)

        self.assertTrue(mock_lcc.called)
        self.assertTrue(mock_connect_api.called)

        expected_targ_section = "apiCalls"
        mock_wcd.assert_called_with(expected_targ_section, expected_dict)

    @patch("GUI.SettingsFrame.SettingsFrame.attempt_connect_to_api")
    def test_save_settings_no_changes(self, mock_connect_api):

        self.frame.log_panel.Clear()
        self.assertEqual(self.frame.log_panel.GetValue(), "")

        push_button(self.frame.save_btn)

        self.assertIn("No changes to save", self.frame.log_panel.GetValue())

        # assert that previous info on log panel was cleared
        expected_num_lines = 2
        # 1 line for "No changes..."
        # 1 line for "\n" at end of message
        self.assertEqual(self.frame.log_panel.GetNumberOfLines(),
                         expected_num_lines)

        assert_boxes_have_neutral_color(self)

        self.assertTrue(mock_connect_api.called)

    @patch("GUI.SettingsFrame.SettingsFrame.write_config_data")
    def test_close_with_unsaved_changes_save(self, mock_wcd):
        new_baseURL = "new_baseURL"
        new_username = "new_username"
        new_password = "new_password"
        new_client_id = "new_client_id"
        new_client_secret = "new_client_secret"

        expected_dict = {"username": new_username,
                         "client_secret": new_client_secret,
                         "password": new_password,
                         "baseURL": new_baseURL,
                         "client_id": new_client_id}

        def handle_prompt_dlg(self):

            self.assertTrue(self.frame.prompt_dlg.IsShown())

            expected_txt = "You have unsaved changes"
            self.assertIn(expected_txt,
                          self.frame.prompt_dlg.Message)
            expected_pw_hidden = "password = {asterisks}".format(
                asterisks=len(new_password) * "*")
            self.assertIn(expected_pw_hidden,
                          self.frame.prompt_dlg.Message)

            self.frame.prompt_dlg.EndModal(wx.ID_YES)  # yes save changes
            self.assertFalse(self.frame.prompt_dlg.IsShown())

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

        handle_func = handle_prompt_dlg
        time_counter = {"value": 0}
        self.frame.timer = wx.Timer(self.frame)
        self.frame.Bind(wx.EVT_TIMER,
                        lambda evt: poll_for_prompt_dlg(self,
                                                        time_counter,
                                                        handle_func),
                        self.frame.timer)
        self.frame.timer.Start(POLL_INTERVAL)

        push_button(self.frame.close_btn)

        assert_boxes_have_neutral_color(self)

        expected_targ_section = "apiCalls"
        mock_wcd.assert_called_with(expected_targ_section, expected_dict)

    @patch("GUI.SettingsFrame.SettingsFrame.write_config_data")
    def test_close_with_unsaved_changes_dont_save(self, mock_wcd):

        new_baseURL = "new_baseURL"
        new_username = "new_username"
        new_password = "new_password"
        new_client_id = "new_client_id"
        new_client_secret = "new_client_secret"

        expected_dict = {"username": new_username,
                         "client_secret": new_client_secret,
                         "password": new_password,
                         "baseURL": new_baseURL,
                         "client_id": new_client_id}

        def handle_prompt_dlg(self):

            self.assertTrue(self.frame.prompt_dlg.IsShown())

            expected_txt = "You have unsaved changes"
            self.assertIn(expected_txt,
                          self.frame.prompt_dlg.Message)
            expected_pw_hidden = "password = {asterisks}".format(
                asterisks=len(new_password) * "*")
            self.assertIn(expected_pw_hidden,
                          self.frame.prompt_dlg.Message)

            self.frame.prompt_dlg.EndModal(wx.ID_NO)  # no don't save changes
            self.assertFalse(self.frame.prompt_dlg.IsShown())

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

        handle_func = handle_prompt_dlg
        time_counter = {"value": 0}
        self.frame.timer = wx.Timer(self.frame)
        self.frame.Bind(wx.EVT_TIMER,
                        lambda evt: poll_for_prompt_dlg(self,
                                                        time_counter,
                                                        handle_func),
                        self.frame.timer)
        self.frame.timer.Start(POLL_INTERVAL)

        push_button(self.frame.close_btn)

        assert_boxes_have_neutral_color(self)

        # reset boxes back to their original values - discard changes
        self.assertEqual(self.frame.base_URL_box.GetValue(),
                         self.frame.config_dict["baseURL"])
        self.assertEqual(self.frame.username_box.GetValue(),
                         self.frame.config_dict["username"])
        self.assertEqual(self.frame.password_box.GetValue(),
                         self.frame.config_dict["password"])
        self.assertEqual(self.frame.client_id_box.GetValue(),
                         self.frame.config_dict["client_id"])
        self.assertEqual(self.frame.client_secret_box.GetValue(),
                         self.frame.config_dict["client_secret"])

        self.assertFalse(mock_wcd.called)

    @patch("GUI.SettingsFrame.ApiCalls")
    def test_debug_invalid_connection(self, mock_apicalls):

        # click the checkbox - it is now checked
        click_checkbox(self.frame.debug_checkbox)

        self.frame.log_panel.Clear()
        self.assertEqual(self.frame.log_panel.GetValue(), "")

        mock_apicalls.side_effect = [ConnectionError()]
        self.frame.attempt_connect_to_api()

        self.assertIn("Cannot connect to url",
                      self.frame.log_panel.GetValue())
        self.assertIn("Message from server", self.frame.log_panel.GetValue())

    @patch("GUI.SettingsFrame.ApiCalls")
    def test_debug_invalid_user_or_pass(self, mock_apicalls):

        click_checkbox(self.frame.debug_checkbox)

        self.frame.log_panel.Clear()
        self.assertEqual(self.frame.log_panel.GetValue(), "")

        mock_apicalls.side_effect = [KeyError("Bad credentials")]
        self.frame.attempt_connect_to_api()

        self.assertIn("Invalid credentials",
                      self.frame.log_panel.GetValue())
        self.assertIn("Username and/or password is incorrect",
                      self.frame.log_panel.GetValue())
        self.assertIn("Message from server", self.frame.log_panel.GetValue())

    @patch("GUI.SettingsFrame.ApiCalls")
    def test_debug_invalid_client_id(self, mock_apicalls):

        click_checkbox(self.frame.debug_checkbox)

        self.frame.log_panel.Clear()
        self.assertEqual(self.frame.log_panel.GetValue(), "")

        mock_apicalls.side_effect = [KeyError("clientId does not exist")]
        self.frame.attempt_connect_to_api()

        self.assertIn("Invalid credentials",
                      self.frame.log_panel.GetValue())
        self.assertIn("Client ID is incorrect",
                      self.frame.log_panel.GetValue())
        self.assertIn("Message from server", self.frame.log_panel.GetValue())

    @patch("GUI.SettingsFrame.ApiCalls")
    def test_debug_invalid_client_secret(self, mock_apicalls):

        click_checkbox(self.frame.debug_checkbox)

        self.frame.log_panel.Clear()
        self.assertEqual(self.frame.log_panel.GetValue(), "")

        mock_apicalls.side_effect = [KeyError("Bad client credentials")]
        self.frame.attempt_connect_to_api()

        self.assertIn("Invalid credentials",
                      self.frame.log_panel.GetValue())
        self.assertIn("Client Secret is incorrect",
                      self.frame.log_panel.GetValue())
        self.assertIn("Message from server", self.frame.log_panel.GetValue())


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
        TestSettingsFrame("test_unexpected_err"))

    gui_sf_test_suite.addTest(
        TestSettingsFrame("test_restore_default_settings"))

    gui_sf_test_suite.addTest(
        TestSettingsFrame("test_save_settings"))
    gui_sf_test_suite.addTest(
        TestSettingsFrame("test_save_settings_no_changes"))

    gui_sf_test_suite.addTest(
        TestSettingsFrame("test_close_with_unsaved_changes_save"))
    gui_sf_test_suite.addTest(
        TestSettingsFrame("test_close_with_unsaved_changes_dont_save"))

    gui_sf_test_suite.addTest(
        TestSettingsFrame("test_debug_invalid_connection"))
    gui_sf_test_suite.addTest(
        TestSettingsFrame("test_debug_invalid_user_or_pass"))
    gui_sf_test_suite.addTest(
        TestSettingsFrame("test_debug_invalid_client_id"))
    gui_sf_test_suite.addTest(
        TestSettingsFrame("test_debug_invalid_client_secret"))

    return gui_sf_test_suite


if __name__ == "__main__":

    sf_ts = load_test_suite()
    full_suite = unittest.TestSuite([sf_ts])

    runner = unittest.TextTestRunner()
    runner.run(full_suite)