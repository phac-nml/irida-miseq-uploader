import unittest
import wx
import re
import traceback
import sys
from os import path, listdir

from GUI.iridaUploaderMain import MainFrame
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


def poll_for_dir_dlg(self, time_counter, poll_warn_dlg=False,
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
        handle_dir_dlg(self, poll_warn_dlg, handle_func)


def handle_dir_dlg(self, poll_warn_dlg, handle_func):

    try:
        self.assertTrue(self.frame.mp.dir_dlg.IsShown())
        self.frame.mp.dir_dlg.EndModal(wx.ID_OK)
        self.assertFalse(self.frame.mp.dir_dlg.IsShown())

        if poll_warn_dlg:
            time_counter2 = {"value": 0}
            self.frame.mp.timer2 = wx.Timer(self.frame.mp)
            self.frame.mp.Bind(wx.EVT_TIMER,
                               lambda evt: poll_for_warn_dlg(
                                self, time_counter2, handle_func),
                               self.frame.mp.timer2)
            self.frame.mp.timer2.Start(POLL_INTERVAL)

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
        self.frame = MainFrame()
        # print self.frame.mp.dir_dlg

    def tearDown(self):

        self.frame.mp.Destroy()
        self.app.Destroy()

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
        self.assertEqual(self.frame.mp.VALID_SAMPLESHEET_BG_COLOR,
                         self.frame.mp.dir_box.GetBackgroundColour())
        self.assertTrue(self.frame.mp.upload_button.IsEnabled())

    def test_sample_sheet_multiple_valid(self):

        time_counter = {"value": 0}

        self.frame.mp.browse_path = path.join(PATH_TO_MODULE,
                                              "testMultiValidSheets", "child")

        self.frame.mp.timer = wx.Timer(self.frame.mp)
        self.frame.mp.Bind(wx.EVT_TIMER,
                           lambda evt: poll_for_dir_dlg(self, time_counter),
                           self.frame.mp.timer)
        self.frame.mp.timer.Start(POLL_INTERVAL)

        push_button(self.frame.mp.browse_button)

        self.assertEqual(self.frame.mp.log_panel.GetValue().count(
                         "SampleSheet.csv is valid"), 2)
        self.assertEqual(self.frame.mp.VALID_SAMPLESHEET_BG_COLOR,
                         self.frame.mp.dir_box.GetBackgroundColour())
        self.assertTrue(self.frame.mp.upload_button.IsEnabled())

    def test_sample_sheet_invalid_no_sheets(self):

        def handle_warn_dlg(self):

            self.assertTrue(self.frame.mp.warn_dlg.IsShown())

            expected_txt = ("SampleSheet.csv file not found in the selected " +
                            "directory:\n" + self.frame.mp.browse_path)
            self.assertIn(expected_txt,
                          self.frame.mp.warn_dlg.Message)

            self.frame.mp.warn_dlg.EndModal(wx.ID_OK)
            self.assertFalse(self.frame.mp.warn_dlg.IsShown())

            self.assertIn(expected_txt, self.frame.mp.log_panel.GetValue())

        time_counter = {"value": 0}
        h_func = handle_warn_dlg  # shorten name to avoid pep8 79 char limit

        self.frame.mp.browse_path = path.join(PATH_TO_MODULE,
                                              "testSampleSheets", "child")
        self.frame.mp.timer = wx.Timer(self.frame.mp)
        self.frame.mp.Bind(wx.EVT_TIMER,
                           lambda evt: poll_for_dir_dlg(self, time_counter,
                                                        poll_warn_dlg=True,
                                                        handle_func=h_func),
                           self.frame.mp.timer)
        self.frame.mp.timer.Start(POLL_INTERVAL)

        push_button(self.frame.mp.browse_button)

        self.assertEqual(self.frame.mp.INVALID_SAMPLESHEET_BG_COLOR,
                         self.frame.mp.dir_box.GetBackgroundColour())
        self.assertFalse(self.frame.mp.upload_button.IsEnabled())

    def test_sample_sheet_invalid_top_sub_ss(self):
        #  samplesheet found in both top of directory and subdirectory

        def handle_warn_dlg(self):

            self.assertTrue(self.frame.mp.warn_dlg.IsShown())

            expected_txt1 = ("Found SampleSheet.csv in both top level " +
                             "directory:\n {t_dir}\nand subdirectory".
                             format(t_dir=self.frame.mp.browse_path))
            self.assertIn(expected_txt1, self.frame.mp.warn_dlg.Message)

            expected_txt2 = ("You can only have either:\n" +
                             "  One SampleSheet.csv on the top level " +
                             "directory\n  Or multiple SampleSheet.csv " +
                             "files in the the subdirectories")
            self.assertIn(expected_txt2, self.frame.mp.warn_dlg.Message)

            self.frame.mp.warn_dlg.EndModal(wx.ID_OK)
            self.assertFalse(self.frame.mp.warn_dlg.IsShown())

            self.assertIn(expected_txt1, self.frame.mp.log_panel.GetValue())
            self.assertIn(expected_txt2, self.frame.mp.log_panel.GetValue())

        time_counter = {"value": 0}
        h_func = handle_warn_dlg

        self.frame.mp.browse_path = path.join(PATH_TO_MODULE,
                                              "testSeqPairFiles", "child")
        self.frame.mp.timer = wx.Timer(self.frame.mp)
        self.frame.mp.Bind(wx.EVT_TIMER,
                           lambda evt: poll_for_dir_dlg(self, time_counter,
                                                        poll_warn_dlg=True,
                                                        handle_func=h_func),
                           self.frame.mp.timer)
        self.frame.mp.timer.Start(POLL_INTERVAL)

        push_button(self.frame.mp.browse_button)

        self.assertEqual(self.frame.mp.INVALID_SAMPLESHEET_BG_COLOR,
                         self.frame.mp.dir_box.GetBackgroundColour())
        self.assertFalse(self.frame.mp.upload_button.IsEnabled())

    def test_sample_sheet_invalid_seqfiles(self):

        def handle_warn_dlg(self):

            self.assertTrue(self.frame.mp.warn_dlg.IsShown())

            expected_txt = "doesn't contain either 'R1' or 'R2' in filename."
            self.assertIn(expected_txt, self.frame.mp.warn_dlg.Message)

            self.frame.mp.warn_dlg.EndModal(wx.ID_OK)
            self.assertFalse(self.frame.mp.warn_dlg.IsShown())

            self.assertIn(expected_txt, self.frame.mp.log_panel.GetValue())

        time_counter = {"value": 0}
        h_func = handle_warn_dlg

        self.frame.mp.browse_path = path.join(
            PATH_TO_MODULE, "testSeqPairFiles", "invalidSeqFiles", "child")

        # using timer because dir_dlg thread is waiting for user input
        self.frame.mp.timer = wx.Timer(self.frame.mp)
        self.frame.mp.Bind(wx.EVT_TIMER,
                           lambda evt: poll_for_dir_dlg(self, time_counter,
                                                        poll_warn_dlg=True,
                                                        handle_func=h_func),
                           self.frame.mp.timer)
        self.frame.mp.timer.Start(POLL_INTERVAL)

        push_button(self.frame.mp.browse_button)

        self.assertEqual(self.frame.mp.INVALID_SAMPLESHEET_BG_COLOR,
                         self.frame.mp.dir_box.GetBackgroundColour())
        self.assertFalse(self.frame.mp.upload_button.IsEnabled())

    def test_sample_sheet_invalid_seqfiles_no_pair(self):

        def handle_warn_dlg(self):

            self.assertTrue(self.frame.mp.warn_dlg.IsShown())

            pattern1 = ("No pair sequence file found for: .+" +
                        re.escape("01-1111_S1_L001_R1_001.fastq.gz"))
            match1 = re.search(pattern1, self.frame.mp.warn_dlg.Message)
            self.assertIsNotNone(match1.group())

            pattern2 = ("Required matching sequence file: .+" +
                        re.escape("01-1111_S1_L001_R2_001.fastq.gz"))
            match2 = re.search(pattern2, self.frame.mp.warn_dlg.Message)
            self.assertIsNotNone(match2.group())

            self.frame.mp.warn_dlg.EndModal(wx.ID_OK)
            self.assertFalse(self.frame.mp.warn_dlg.IsShown())

            match3 = re.search(pattern1, self.frame.mp.log_panel.GetValue())
            match4 = re.search(pattern2, self.frame.mp.log_panel.GetValue())

            self.assertIsNotNone(match3.group())
            self.assertIsNotNone(match4.group())

        time_counter = {"value": 0}
        h_func = handle_warn_dlg

        self.frame.mp.browse_path = path.join(
            PATH_TO_MODULE, "testSeqPairFiles", "noPair", "child")

        self.frame.mp.timer = wx.Timer(self.frame.mp)
        self.frame.mp.Bind(wx.EVT_TIMER,
                           lambda evt: poll_for_dir_dlg(self, time_counter,
                                                        poll_warn_dlg=True,
                                                        handle_func=h_func),
                           self.frame.mp.timer)
        self.frame.mp.timer.Start(POLL_INTERVAL)

        push_button(self.frame.mp.browse_button)

        self.assertEqual(self.frame.mp.INVALID_SAMPLESHEET_BG_COLOR,
                         self.frame.mp.dir_box.GetBackgroundColour())
        self.assertFalse(self.frame.mp.upload_button.IsEnabled())

    def test_sample_sheet_invalid_seqfiles_odd_len(self):

        def handle_warn_dlg(self):

            self.assertTrue(self.frame.mp.warn_dlg.IsShown())

            expected_txt1 = "The given file list has an odd number of files."
            expected_txt2 = ("Requires an even number of files " +
                             "in order for each sequence file to have a pair.")

            self.assertIn(expected_txt1, self.frame.mp.warn_dlg.Message)
            self.assertIn(expected_txt2, self.frame.mp.warn_dlg.Message)

            self.frame.mp.warn_dlg.EndModal(wx.ID_OK)
            self.assertFalse(self.frame.mp.warn_dlg.IsShown())

            self.assertIn(expected_txt1, self.frame.mp.log_panel.GetValue())
            self.assertIn(expected_txt2, self.frame.mp.log_panel.GetValue())

        time_counter = {"value": 0}
        h_func = handle_warn_dlg

        self.frame.mp.browse_path = path.join(
            PATH_TO_MODULE, "testSeqPairFiles", "oddLength", "child")
        self.frame.mp.timer = wx.Timer(self.frame.mp)
        self.frame.mp.Bind(wx.EVT_TIMER,
                           lambda evt: poll_for_dir_dlg(self, time_counter,
                                                        poll_warn_dlg=True,
                                                        handle_func=h_func),
                           self.frame.mp.timer)
        self.frame.mp.timer.Start(POLL_INTERVAL)

        push_button(self.frame.mp.browse_button)

        self.assertEqual(self.frame.mp.INVALID_SAMPLESHEET_BG_COLOR,
                         self.frame.mp.dir_box.GetBackgroundColour())
        self.assertFalse(self.frame.mp.upload_button.IsEnabled())

    @patch("GUI.SettingsFrame.pub")
    @patch(
        "GUI.SettingsFrame.SettingsPanel.attempt_connect_to_api")
    def test_open_settings(self, mock_connect_api, mock_pub_sub):

        menu_evt = wx.PyCommandEvent(wx.EVT_MENU.typeId,
                                     self.frame.OPEN_SETTINGS_ID)
        self.frame.mp.GetEventHandler().ProcessEvent(menu_evt)
        self.assertTrue(self.frame.mp.settings_frame.IsShown())

        push_button(self.frame.mp.settings_frame.close_btn)
        self.assertFalse(self.frame.mp.settings_frame.IsShown())


def load_test_suite():

    gui_test_suite = unittest.TestSuite()

    gui_test_suite.addTest(
        TestIridaUploaderMain("test_sample_sheet_valid"))
    gui_test_suite.addTest(
        TestIridaUploaderMain("test_sample_sheet_multiple_valid"))
    gui_test_suite.addTest(
        TestIridaUploaderMain("test_sample_sheet_invalid_no_sheets"))
    gui_test_suite.addTest(
        TestIridaUploaderMain("test_sample_sheet_invalid_top_sub_ss"))
    gui_test_suite.addTest(
        TestIridaUploaderMain("test_sample_sheet_invalid_seqfiles"))
    gui_test_suite.addTest(
        TestIridaUploaderMain("test_sample_sheet_invalid_seqfiles_no_pair"))
    gui_test_suite.addTest(
        TestIridaUploaderMain("test_sample_sheet_invalid_seqfiles_odd_len"))
    gui_test_suite.addTest(
        TestIridaUploaderMain("test_open_settings"))

    return gui_test_suite


if __name__ == "__main__":

    test_suite = load_test_suite()
    full_suite = unittest.TestSuite([test_suite])

    runner = unittest.TextTestRunner()
    runner.run(full_suite)
