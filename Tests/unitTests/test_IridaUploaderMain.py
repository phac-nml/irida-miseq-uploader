import unittest
import wx
import re
import traceback
import sys
from os import path

from GUI.MainFrame import MainFrame
from GUI.MainPanel import MainPanel
from mock import patch

PATH_TO_MODULE = path.dirname(path.abspath(__file__))
POLL_INTERVAL = 100  # milliseconds
MAX_WAIT_TIME = 5000  # milliseconds


def push_button(targ_obj):
    """
    helper function that sends the event wx.EVT_BUTTON to the given targ_obj
    """
    button_evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, targ_obj.GetId())
    targ_obj.GetEventHandler().ProcessEvent(button_evt)


def poll_for_dir_dlg(self, time_counter,
                     handle_func=None):
    """
    poll_warn_dlg and handle_func are used by functions that are expecting
    to see a warning dialog because they are testing for the error messages
    that are inside warn_dlg
    """

    time_counter["value"] += POLL_INTERVAL

    if (self.frame.mp.dir_dlg is not None or
            time_counter["value"] == MAX_WAIT_TIME):
        self.frame.mp.timer.Stop()
        handle_dir_dlg(self, handle_func)


def handle_dir_dlg(self, handle_func):

    try:
        self.assertTrue(self.frame.mp.dir_dlg.IsShown())
        self.frame.mp.dir_dlg.EndModal(wx.ID_OK)
        self.assertFalse(self.frame.mp.dir_dlg.IsShown())

    except (AssertionError, AttributeError):
        print traceback.format_exc()
        sys.exit(1)


def poll_for_warn_dlg(self, time_counter2, handle_func):

    time_counter2["value"] += POLL_INTERVAL

    if (hasattr(self.frame.mp, "warn_dlg") or
            time_counter2["value"] == MAX_WAIT_TIME):
        self.frame.mp.timer2.Stop()

        try:
            handle_func(self)

        except (AssertionError, AttributeError):
            print traceback.format_exc()
            sys.exit(1)


class TestIridaUploaderMain(unittest.TestCase):

    def setUp(self):

        print "\nStarting " + self.__module__ + ": " + self._testMethodName
        self.app = wx.App(False)
        # print self.frame.mp.dir_dlg

    def tearDown(self):

        self.frame.mp.Destroy()
        self.app.Destroy()

    @patch.object(MainPanel, "get_config_default_dir", lambda self: path.join(PATH_TO_MODULE, "fake_ngs_data"))
    def test_sample_sheet_valid(self):

        """
        self.frame.mp.timer calls poll_for_dir_dlg() once every POLL_INTERVAL
            milliseconds.

        poll_for_dir_dlg() checks if the dir_dlg (select directory dialog) is
            no longer None (i.e if it has been created) and if so then call
            handle_dir_dlg for checking assertions etc.

        if the MAX_WAIT_TIME is reached, handle_dir_dlg will still be
            called and if self.frame.mp.dir_dlg is still None then an
            AttributeError will be raised

        if assertions fail inside the functions that are in a different thread
            (handle_dir_dlg, poll_for_warn_dlg,
             handle_warn_dlg/handle_func) then an AssertionError will be raised

        Both AssertionError and AttributeError raised inside those threads will
        print a traceback of what caused them to be raised and then calls
        sys.exit to prevent the GUI program from hanging waiting for input
        """
        time_counter = {"value": 0}
        self.frame = MainFrame()

        # dir_dlg uses parent of browse_path; need /child to get /fake_ngs_data
        self.frame.mp.browse_path = path.join(PATH_TO_MODULE, "fake_ngs_data",
                                              "child")
        self.frame.mp.timer = wx.Timer(self.frame.mp)
        self.frame.mp.Bind(wx.EVT_TIMER,
                           lambda evt: poll_for_dir_dlg(self, time_counter),
                           self.frame.mp.timer)
        self.frame.mp.timer.Start(POLL_INTERVAL)

        push_button(self.frame.mp.browse_button)

        self.assertIn("SampleSheet.csv is valid",
                      self.frame.mp.log_panel.GetValue())
        self.assertTrue(self.frame.mp.upload_button.IsEnabled())

    @patch.object(MainPanel, "get_config_default_dir", lambda self: path.join(PATH_TO_MODULE, "testMultiValidSheets"))
    def test_sample_sheet_multiple_valid(self):

        time_counter = {"value": 0}

        self.frame = MainFrame()

        self.frame.mp.timer = wx.Timer(self.frame.mp)
        self.frame.mp.Bind(wx.EVT_TIMER,
                           lambda evt: poll_for_dir_dlg(self, time_counter),
                           self.frame.mp.timer)
        self.frame.mp.timer.Start(POLL_INTERVAL)

        self.assertEqual(self.frame.mp.log_panel.GetValue().count(
                         "SampleSheet.csv is valid"), 2)
        self.assertTrue(self.frame.mp.upload_button.IsEnabled())

    @patch.object(MainPanel, "get_config_default_dir", lambda self: path.join(PATH_TO_MODULE, "testSampleSheets"))
    def test_sample_sheet_invalid_no_sheets(self):

        def handle_warn_dlg(self):

            expected_txt = ("SampleSheet.csv file not found in the selected " +
                            "directory:\n" + self.frame.mp.browse_path)
            self.assertIn(expected_txt, self.frame.mp.log_panel.GetValue())

        time_counter = {"value": 0}
        self.frame = MainFrame()
        h_func = handle_warn_dlg  # shorten name to avoid pep8 79 char limit

        self.frame.mp.browse_path = path.join(PATH_TO_MODULE,
                                              "testSampleSheets", "child")
        self.frame.mp.timer = wx.Timer(self.frame.mp)
        self.frame.mp.Bind(wx.EVT_TIMER,
                           lambda evt: poll_for_dir_dlg(self, time_counter,
                                                        handle_func=h_func),
                           self.frame.mp.timer)
        self.frame.mp.timer.Start(POLL_INTERVAL)

        push_button(self.frame.mp.browse_button)

        self.assertFalse(self.frame.mp.upload_button.IsEnabled())

def load_test_suite():

    gui_test_suite = unittest.TestSuite()

    gui_test_suite.addTest(
        TestIridaUploaderMain("test_sample_sheet_valid"))
    gui_test_suite.addTest(
        TestIridaUploaderMain("test_sample_sheet_multiple_valid"))
    gui_test_suite.addTest(
        TestIridaUploaderMain("test_sample_sheet_invalid_no_sheets"))

    return gui_test_suite


if __name__ == "__main__":

    test_suite = load_test_suite()
    full_suite = unittest.TestSuite([test_suite])

    runner = unittest.TextTestRunner()
    runner.run(full_suite)
