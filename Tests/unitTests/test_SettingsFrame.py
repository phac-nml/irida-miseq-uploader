import unittest
import wx
import traceback
import sys
from requests.exceptions import ConnectionError
from collections import OrderedDict
import GUI.SettingsFrame
from mock import patch


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


def poll_for_prompt_dlg(self, time_counter, handle_func):

    time_counter["value"] += POLL_INTERVAL

    if (self.frame.sp.prompt_dlg is not None or
            time_counter["value"] == MAX_WAIT_TIME):
        self.frame.sp.timer.Stop()

        try:

            handle_func(self)

        except (AssertionError, AttributeError):
            print traceback.format_exc()
            sys.exit(1)


class TestSettingsFrame(unittest.TestCase):

    def set_config_dict(self):

        self.frame.sp.config_dict = OrderedDict()
        self.frame.sp.config_dict["baseURL"] = "http://localhost:8080/api2"
        self.frame.sp.config_dict["username"] = "admin2"
        self.frame.sp.config_dict["password"] = "password2"
        self.frame.sp.config_dict["client_id"] = "testClient2"
        self.frame.sp.config_dict["client_secret"] = "testSecret2"
        self.frame.sp.config_dict["completion_cmd"] = "echo 2"

    def set_boxes(self):

        self.frame.sp.base_url_box.SetValue(
            self.frame.sp.config_dict["baseURL"])
        self.frame.sp.username_box.SetValue(
            self.frame.sp.config_dict["username"])
        self.frame.sp.password_box.SetValue(
            self.frame.sp.config_dict["password"])
        self.frame.sp.client_id_box.SetValue(
            self.frame.sp.config_dict["client_id"])
        self.frame.sp.client_secret_box.SetValue(
            self.frame.sp.config_dict["client_secret"])
        self.frame.sp.completion_cmd_box.SetValue(
            self.frame.sp.config_dict["completion_cmd"])

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

        # self.frame.sp.Show()

    def tearDown(self):

        self.frame.Destroy()
        self.app.Destroy()

    @patch("GUI.SettingsFrame.ApiCalls")
    def test_valid_credentials(self, mock_apicalls):

        self.frame.sp.attempt_connect_to_api()

        self.assertIn("Successfully connected to API",
                      self.frame.sp.log_panel.GetValue())

        self.assertEqual(self.frame.sp.base_url_suc_icon.Label, "success")
        self.assertEqual(self.frame.sp.username_suc_icon.Label, "success")
        self.assertEqual(self.frame.sp.password_suc_icon.Label, "success")
        self.assertEqual(self.frame.sp.client_id_suc_icon.Label, "success")
        self.assertEqual(self.frame.sp.client_secret_suc_icon.Label, "success")

        self.assertEqual(self.frame.sp.base_url_warn_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.username_warn_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.password_warn_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.client_id_warn_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.client_secret_warn_icon.Label, "hidden")

    @patch("GUI.SettingsFrame.ApiCalls")
    def test_invalid_connection(self, mock_apicalls):

        mock_apicalls.side_effect = [ConnectionError()]
        self.frame.sp.attempt_connect_to_api()

        self.assertIn("Cannot connect to url",
                      self.frame.sp.log_panel.GetValue())
        self.assertNotIn("Message from server",
                         self.frame.sp.log_panel.GetValue())

        self.assertEqual(self.frame.sp.base_url_suc_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.username_suc_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.password_suc_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.client_id_suc_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.client_secret_suc_icon.Label, "hidden")

        self.assertEqual(self.frame.sp.base_url_warn_icon.Label, "warning")
        self.assertEqual(self.frame.sp.username_warn_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.password_warn_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.client_id_warn_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.client_secret_warn_icon.Label, "hidden")

    @patch("GUI.SettingsFrame.ApiCalls")
    def test_key_err_invalid_user_or_pass(self, mock_apicalls):

        mock_apicalls.side_effect = [KeyError("Bad credentials")]
        self.frame.sp.attempt_connect_to_api()

        self.assertIn("Invalid credentials",
                      self.frame.sp.log_panel.GetValue())
        self.assertIn("Username and/or password is incorrect",
                      self.frame.sp.log_panel.GetValue())
        self.assertNotIn("Message from server",
                         self.frame.sp.log_panel.GetValue())

        self.assertEqual(self.frame.sp.base_url_suc_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.username_suc_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.password_suc_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.client_id_suc_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.client_secret_suc_icon.Label, "hidden")

        self.assertEqual(self.frame.sp.base_url_warn_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.username_warn_icon.Label, "warning")
        self.assertEqual(self.frame.sp.password_warn_icon.Label, "warning")
        self.assertEqual(self.frame.sp.client_id_warn_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.client_secret_warn_icon.Label, "hidden")

    @patch("GUI.SettingsFrame.ApiCalls")
    def test_key_err_invalid_client_id(self, mock_apicalls):

        mock_apicalls.side_effect = [KeyError("clientId does not exist")]
        self.frame.sp.attempt_connect_to_api()

        self.assertIn("Invalid credentials",
                      self.frame.sp.log_panel.GetValue())
        self.assertIn("Client ID is incorrect",
                      self.frame.sp.log_panel.GetValue())
        self.assertNotIn("Message from server",
                         self.frame.sp.log_panel.GetValue())

        self.assertEqual(self.frame.sp.base_url_suc_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.username_suc_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.password_suc_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.client_id_suc_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.client_secret_suc_icon.Label, "hidden")

        self.assertEqual(self.frame.sp.base_url_warn_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.username_warn_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.password_warn_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.client_id_warn_icon.Label, "warning")
        self.assertEqual(self.frame.sp.client_secret_warn_icon.Label, "hidden")

    @patch("GUI.SettingsFrame.ApiCalls")
    def test_key_err_invalid_client_secret(self, mock_apicalls):

        mock_apicalls.side_effect = [KeyError("Bad client credentials")]
        self.frame.sp.attempt_connect_to_api()

        self.assertIn("Invalid credentials",
                      self.frame.sp.log_panel.GetValue())
        self.assertIn("Client Secret is incorrect",
                      self.frame.sp.log_panel.GetValue())
        self.assertNotIn("Message from server",
                         self.frame.sp.log_panel.GetValue())

        self.assertEqual(self.frame.sp.base_url_suc_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.username_suc_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.password_suc_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.client_id_suc_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.client_secret_suc_icon.Label, "hidden")

        self.assertEqual(self.frame.sp.base_url_suc_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.username_suc_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.password_suc_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.client_id_suc_icon.Label, "hidden")
        self.assertEqual(
            self.frame.sp.client_secret_warn_icon.Label, "warning")

    @patch("GUI.SettingsFrame.ApiCalls")
    def test_value_err(self, mock_apicalls):

        mock_apicalls.side_effect = [ValueError()]
        self.frame.sp.attempt_connect_to_api()

        self.assertIn("Cannot connect to url",
                      self.frame.sp.log_panel.GetValue())
        self.assertNotIn("Message from server",
                         self.frame.sp.log_panel.GetValue())

        self.assertEqual(self.frame.sp.base_url_warn_icon.Label, "warning")
        self.assertEqual(self.frame.sp.username_suc_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.password_suc_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.client_id_suc_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.client_secret_suc_icon.Label, "hidden")

    @patch("GUI.SettingsFrame.ApiCalls")
    def test_unexpected_err(self, mock_apicalls):

        mock_apicalls.side_effect = [SyntaxError()]
        self.frame.sp.attempt_connect_to_api()

        self.assertIn("Unexpected error",
                      self.frame.sp.log_panel.GetValue())

        self.assertEqual(self.frame.sp.base_url_suc_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.username_suc_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.password_suc_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.client_id_suc_icon.Label, "hidden")
        self.assertEqual(self.frame.sp.client_secret_suc_icon.Label, "hidden")
