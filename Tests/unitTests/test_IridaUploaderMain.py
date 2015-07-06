import unittest
import wx
import re
from os import path, listdir

from GUI.iridaUploaderMain import MainFrame

path_to_module = path.dirname(path.abspath(__file__))


def push_button(targ_obj):
    """
    helper function that sends the event wx.EVT_BUTTON to the given targ_obj
    """
    button_evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, targ_obj.GetId())
    targ_obj.GetEventHandler().ProcessEvent(button_evt)


class TestIridaUploaderMain(unittest.TestCase):

    def setUp(self):

        print "\nStarting " + self.__module__ + ": " + self._testMethodName
        self.app = wx.App(False)
        self.frame = MainFrame()
        self.WAIT_TIME = 2500
        self.POLL_INTERVAL = 1  # milliseconds
        self.MAX_WAIT_TIME = 5000  # milliseconds

    def tearDown(self):

        self.frame.Destroy()
        self.app.Destroy()

    def test_open_sample_sheet(self):

        """
        self.frame.timer calls poll_for_dir_dlg() once every self.POLL_INTERVAL
            milliseconds.
        poll_for_dir_dlg() checks if the dir_dlg (select directory dialog) is
            no longer None (i.e if it has been created) and if so then call
            handle_dir_dlg for checking assertions etc.
            if the self.MAX_WAIT_TIME is reached, handle_dir_dlg will still be
            called and the assertions will naturally fail because
            self.frame.dir_dlg is still None

        using time_counter as dict because ints are immutable and didn't want
        to attach it to self in case it might get used by another function
        """

        def poll_for_dir_dlg(self, evt, time_counter):

            time_counter["value"] += self.POLL_INTERVAL

            if (self.frame.dir_dlg is not None or
                    time_counter["value"] == self.MAX_WAIT_TIME):
                self.frame.timer.Stop()
                handle_dir_dlg(self)

        def handle_dir_dlg(self):

            self.assertTrue(self.frame.dir_dlg.IsShown())
            self.frame.dir_dlg.EndModal(wx.ID_CANCEL)

        time_counter = {"value": 0}

        # using timer because dir_dlg thread is waiting for user input
        self.frame.timer = wx.Timer(self.frame)
        self.frame.Bind(wx.EVT_TIMER,
                        lambda evt: poll_for_dir_dlg(self, evt, time_counter),
                        self.frame.timer)
        self.frame.timer.Start(self.POLL_INTERVAL)

        push_button(self.frame.browse_button)

    def test_sample_sheet_valid(self):

        def poll_for_dir_dlg(self, evt, time_counter):

            time_counter["value"] += self.POLL_INTERVAL

            if (self.frame.dir_dlg is not None or
                    time_counter["value"] == self.MAX_WAIT_TIME):
                self.frame.timer.Stop()
                handle_dir_dlg(self)

        def handle_dir_dlg(self):

            self.assertTrue(self.frame.dir_dlg.IsShown())
            self.frame.dir_dlg.EndModal(wx.ID_OK)
            self.assertFalse(self.frame.dir_dlg.IsShown())

        time_counter = {"value": 0}

        # dir_dlg uses parent of browse_path; need /child to get /fake_ngs_data
        self.frame.browse_path = path.join(path_to_module, "fake_ngs_data",
                                           "child")
        self.frame.timer = wx.Timer(self.frame)
        self.frame.Bind(wx.EVT_TIMER,
                        lambda evt: poll_for_dir_dlg(self, evt, time_counter),
                        self.frame.timer)
        self.frame.timer.Start(self.POLL_INTERVAL)

        push_button(self.frame.browse_button)

        self.assertIn("SampleSheet.csv is valid",
                      self.frame.log_panel.GetValue())
        self.assertEqual(self.frame.VALID_SAMPLESHEET_BG_COLOR,
                         self.frame.dir_box.GetBackgroundColour())
        self.assertTrue(self.frame.upload_button.IsEnabled())

    def test_sample_sheet_multiple_valid(self):

        def poll_for_dir_dlg(self, evt, time_counter):

            time_counter["value"] += self.POLL_INTERVAL

            if (self.frame.dir_dlg is not None or
                    time_counter["value"] == self.MAX_WAIT_TIME):
                self.frame.timer.Stop()
                handle_dir_dlg(self)

        def handle_dir_dlg(self):

            self.assertTrue(self.frame.dir_dlg.IsShown())
            self.frame.dir_dlg.EndModal(wx.ID_OK)
            self.assertFalse(self.frame.dir_dlg.IsShown())

        time_counter = {"value": 0}

        self.frame.browse_path = path.join(path_to_module,
                                           "testMultiValidSheets", "child")

        self.frame.timer = wx.Timer(self.frame)
        self.frame.Bind(wx.EVT_TIMER,
                        lambda evt: poll_for_dir_dlg(self, evt, time_counter),
                        self.frame.timer)
        self.frame.timer.Start(self.POLL_INTERVAL)

        push_button(self.frame.browse_button)

        self.assertEqual(self.frame.log_panel.GetValue().count(
                         "SampleSheet.csv is valid"), 2)
        self.assertEqual(self.frame.VALID_SAMPLESHEET_BG_COLOR,
                         self.frame.dir_box.GetBackgroundColour())
        self.assertTrue(self.frame.upload_button.IsEnabled())

    def test_sample_sheet_invalid_no_sheets(self):

        def poll_for_dir_dlg(self, evt, time_counter):

            time_counter["value"] += self.POLL_INTERVAL

            if (self.frame.dir_dlg is not None or
                    time_counter["value"] == self.MAX_WAIT_TIME):
                self.frame.timer.Stop()
                handle_dir_dlg(self)

        def handle_dir_dlg(self):

            self.assertTrue(self.frame.dir_dlg.IsShown())
            self.frame.dir_dlg.EndModal(wx.ID_OK)
            self.assertFalse(self.frame.dir_dlg.IsShown())

            time_counter2 = {"value": 0}
            self.frame.timer2 = wx.Timer(self.frame)
            self.frame.Bind(wx.EVT_TIMER,
                            lambda evt: poll_for_warn_dlg(self,
                                                          evt,
                                                          time_counter2),
                            self.frame.timer2)
            self.frame.timer2.Start(self.POLL_INTERVAL)

        def poll_for_warn_dlg(self, evt, time_counter2):

            time_counter2["value"] += self.POLL_INTERVAL
            if (self.frame.dir_dlg is not None or
                    time_counter2["value"] == self.MAX_WAIT_TIME):
                self.frame.timer2.Stop()
                handle_warn_dlg(self)

        def handle_warn_dlg(self):

            self.assertTrue(self.frame.warn_dlg.IsShown())

            expected_txt = ("SampleSheet.csv file not found in the selected " +
                            "directory:\n" + self.frame.browse_path)
            self.assertIn(expected_txt,
                          self.frame.warn_dlg.Message)

            self.frame.warn_dlg.EndModal(wx.ID_OK)
            self.assertFalse(self.frame.warn_dlg.IsShown())

            self.assertIn(expected_txt, self.frame.log_panel.GetValue())

        time_counter = {"value": 0}

        self.frame.browse_path = path.join(path_to_module,
                                           "testSampleSheets", "child")
        self.frame.timer = wx.Timer(self.frame)
        self.frame.Bind(wx.EVT_TIMER,
                        lambda evt: poll_for_dir_dlg(self, evt, time_counter),
                        self.frame.timer)
        self.frame.timer.Start(self.POLL_INTERVAL)

        push_button(self.frame.browse_button)

        self.assertEqual(self.frame.INVALID_SAMPLESHEET_BG_COLOR,
                         self.frame.dir_box.GetBackgroundColour())
        self.assertFalse(self.frame.upload_button.IsEnabled())

    def test_sample_sheet_invalid_top_sub_ss(self):
        #  samplesheet found in both top of directory and subdirectory

        def poll_for_dir_dlg(self, evt, time_counter):

            time_counter["value"] += self.POLL_INTERVAL

            if (self.frame.dir_dlg is not None or
                    time_counter["value"] == self.MAX_WAIT_TIME):
                self.frame.timer.Stop()
                handle_dir_dlg(self)

        def handle_dir_dlg(self):

            self.assertTrue(self.frame.dir_dlg.IsShown())
            self.frame.dir_dlg.EndModal(wx.ID_OK)
            self.assertFalse(self.frame.dir_dlg.IsShown())

            time_counter2 = {"value": 0}
            self.frame.timer2 = wx.Timer(self.frame)
            self.frame.Bind(wx.EVT_TIMER,
                            lambda evt: poll_for_warn_dlg(self,
                                                          evt,
                                                          time_counter2),
                            self.frame.timer2)
            self.frame.timer2.Start(self.POLL_INTERVAL)

        def poll_for_warn_dlg(self, evt, time_counter2):

            time_counter2["value"] += self.POLL_INTERVAL
            if (self.frame.dir_dlg is not None or
                    time_counter2["value"] == self.MAX_WAIT_TIME):
                self.frame.timer2.Stop()
                handle_warn_dlg(self)

        def handle_warn_dlg(self):

            self.assertTrue(self.frame.warn_dlg.IsShown())

            expected_txt1 = ("Found SampleSheet.csv in both top level " +
                             "directory:\n {t_dir}\nand subdirectory".
                             format(t_dir=self.frame.browse_path))
            self.assertIn(expected_txt1, self.frame.warn_dlg.Message)

            expected_txt2 = ("You can only have either:\n" +
                             "  One SampleSheet.csv on the top level " +
                             "directory\n  Or multiple SampleSheet.csv " +
                             "files in the the subdirectories")
            self.assertIn(expected_txt2, self.frame.warn_dlg.Message)

            self.frame.warn_dlg.EndModal(wx.ID_OK)
            self.assertFalse(self.frame.warn_dlg.IsShown())

            self.assertIn(expected_txt1, self.frame.log_panel.GetValue())
            self.assertIn(expected_txt2, self.frame.log_panel.GetValue())

        time_counter = {"value": 0}

        self.frame.browse_path = path.join(path_to_module,
                                           "testSeqPairFiles", "child")
        self.frame.timer = wx.Timer(self.frame)
        self.frame.Bind(wx.EVT_TIMER,
                        lambda evt: poll_for_dir_dlg(self, evt, time_counter),
                        self.frame.timer)
        self.frame.timer.Start(self.POLL_INTERVAL)

        push_button(self.frame.browse_button)

        self.assertEqual(self.frame.INVALID_SAMPLESHEET_BG_COLOR,
                         self.frame.dir_box.GetBackgroundColour())
        self.assertFalse(self.frame.upload_button.IsEnabled())

    def test_sample_sheet_invalid_seqfiles(self):

        def handle_dir_dlg(self, evt):

            self.assertTrue(self.frame.dir_dlg.IsShown())
            self.frame.dir_dlg.EndModal(wx.ID_OK)
            self.assertFalse(self.frame.dir_dlg.IsShown())

            self.frame.timer2 = wx.Timer(self.frame)
            self.frame.Bind(wx.EVT_TIMER,
                            lambda evt: handle_warn_dlg(self, evt),
                            self.frame.timer2)
            self.frame.timer2.Start(self.WAIT_TIME, oneShot=True)

        def handle_warn_dlg(self, evt):

            self.assertTrue(self.frame.warn_dlg.IsShown())

            expected_txt = "doesn't contain either 'R1' or 'R2' in filename."
            self.assertIn(expected_txt, self.frame.warn_dlg.Message)

            self.frame.warn_dlg.EndModal(wx.ID_OK)
            self.assertFalse(self.frame.warn_dlg.IsShown())

            self.assertIn(expected_txt, self.frame.log_panel.GetValue())

        self.frame.browse_path = path.join(path_to_module, "testSeqPairFiles",
                                           "invalidSeqFiles", "child")

        # using timer because dir_dlg thread is waiting for user input
        self.frame.timer = wx.Timer(self.frame)
        self.frame.Bind(wx.EVT_TIMER,
                        lambda evt: handle_dir_dlg(self, evt),
                        self.frame.timer)
        self.frame.timer.Start(self.WAIT_TIME, oneShot=True)

        push_button(self.frame.browse_button)

        self.assertEqual(self.frame.INVALID_SAMPLESHEET_BG_COLOR,
                         self.frame.dir_box.GetBackgroundColour())
        self.assertFalse(self.frame.upload_button.IsEnabled())

    def test_sample_sheet_invalid_seqfiles_no_pair(self):

        def handle_dir_dlg(self, evt):

            self.assertTrue(self.frame.dir_dlg.IsShown())
            self.frame.dir_dlg.EndModal(wx.ID_OK)
            self.assertFalse(self.frame.dir_dlg.IsShown())

            self.frame.timer2 = wx.Timer(self.frame)
            self.frame.Bind(wx.EVT_TIMER,
                            lambda evt: handle_warn_dlg(self, evt),
                            self.frame.timer2)
            self.frame.timer2.Start(self.WAIT_TIME, oneShot=True)

        def handle_warn_dlg(self, evt):

            self.assertTrue(self.frame.warn_dlg.IsShown())

            pattern1 = ("No pair sequence file found for: .+" +
                        re.escape("01-1111_S1_L001_R1_001.fastq.gz"))
            match1 = re.search(pattern1, self.frame.warn_dlg.Message)
            self.assertIsNotNone(match1.group())

            pattern2 = ("Required matching sequence file: .+" +
                        re.escape("01-1111_S1_L001_R2_001.fastq.gz"))
            match2 = re.search(pattern2, self.frame.warn_dlg.Message)
            self.assertIsNotNone(match2.group())

            self.frame.warn_dlg.EndModal(wx.ID_OK)
            self.assertFalse(self.frame.warn_dlg.IsShown())

            match3 = re.search(pattern1, self.frame.log_panel.GetValue())
            match4 = re.search(pattern2, self.frame.log_panel.GetValue())

            self.assertIsNotNone(match3.group())
            self.assertIsNotNone(match4.group())

        self.frame.browse_path = path.join(path_to_module, "testSeqPairFiles",
                                           "noPair", "child")

        # using timer because dir_dlg thread is waiting for user input
        self.frame.timer = wx.Timer(self.frame)
        self.frame.Bind(wx.EVT_TIMER,
                        lambda evt: handle_dir_dlg(self, evt),
                        self.frame.timer)
        self.frame.timer.Start(self.WAIT_TIME, oneShot=True)

        push_button(self.frame.browse_button)

        self.assertEqual(self.frame.INVALID_SAMPLESHEET_BG_COLOR,
                         self.frame.dir_box.GetBackgroundColour())
        self.assertFalse(self.frame.upload_button.IsEnabled())

    def test_sample_sheet_invalid_seqfiles_odd_len(self):

        def handle_dir_dlg(self, evt):

            self.assertTrue(self.frame.dir_dlg.IsShown())
            self.frame.dir_dlg.EndModal(wx.ID_OK)
            self.assertFalse(self.frame.dir_dlg.IsShown())

            self.frame.timer2 = wx.Timer(self.frame)
            self.frame.Bind(wx.EVT_TIMER,
                            lambda evt: handle_warn_dlg(self, evt),
                            self.frame.timer2)
            self.frame.timer2.Start(self.WAIT_TIME, oneShot=True)

        def handle_warn_dlg(self, evt):

            self.assertTrue(self.frame.warn_dlg.IsShown())

            expected_txt1 = "The given file list has an odd number of files."
            expected_txt2 = ("Requires an even number of files " +
                             "in order for each sequence file to have a pair.")

            self.assertIn(expected_txt1, self.frame.warn_dlg.Message)
            self.assertIn(expected_txt2, self.frame.warn_dlg.Message)

            self.frame.warn_dlg.EndModal(wx.ID_OK)
            self.assertFalse(self.frame.warn_dlg.IsShown())

            self.assertIn(expected_txt1, self.frame.log_panel.GetValue())
            self.assertIn(expected_txt2, self.frame.log_panel.GetValue())

        self.frame.browse_path = path.join(path_to_module, "testSeqPairFiles",
                                           "oddLength", "child")

        # using timer because dir_dlg thread is waiting for user input
        self.frame.timer = wx.Timer(self.frame)
        self.frame.Bind(wx.EVT_TIMER,
                        lambda evt: handle_dir_dlg(self, evt),
                        self.frame.timer)
        self.frame.timer.Start(self.WAIT_TIME, oneShot=True)

        push_button(self.frame.browse_button)

        self.assertEqual(self.frame.INVALID_SAMPLESHEET_BG_COLOR,
                         self.frame.dir_box.GetBackgroundColour())
        self.assertFalse(self.frame.upload_button.IsEnabled())

    def test_sample_sheet_invalid_seqfiles_no_project(self):

        def handle_dir_dlg(self, evt):

            self.assertTrue(self.frame.dir_dlg.IsShown())
            self.frame.dir_dlg.EndModal(wx.ID_OK)
            self.assertFalse(self.frame.dir_dlg.IsShown())

            self.frame.timer2 = wx.Timer(self.frame)
            self.frame.Bind(wx.EVT_TIMER,
                            lambda evt: handle_warn_dlg(self, evt),
                            self.frame.timer2)
            self.frame.timer2.Start(self.WAIT_TIME, oneShot=True)

        def handle_warn_dlg(self, evt):

            self.assertTrue(self.frame.warn_dlg.IsShown())

            expected_txt = "Missing required data header(s): Sample_Project"

            self.assertIn(expected_txt, self.frame.warn_dlg.Message)

            self.frame.warn_dlg.EndModal(wx.ID_OK)
            self.assertFalse(self.frame.warn_dlg.IsShown())

            self.assertIn(expected_txt, self.frame.log_panel.GetValue())

        self.frame.browse_path = path.join(path_to_module, "testSeqPairFiles",
                                           "noSampleProj", "child")

        # using timer because dir_dlg thread is waiting for user input
        self.frame.timer = wx.Timer(self.frame)
        self.frame.Bind(wx.EVT_TIMER,
                        lambda evt: handle_dir_dlg(self, evt),
                        self.frame.timer)
        self.frame.timer.Start(self.WAIT_TIME, oneShot=True)

        push_button(self.frame.browse_button)

        self.assertEqual(self.frame.INVALID_SAMPLESHEET_BG_COLOR,
                         self.frame.dir_box.GetBackgroundColour())
        self.assertFalse(self.frame.upload_button.IsEnabled())

    def test_open_settings(self):

        push_button(self.frame.settings_button)
        self.assertTrue(self.frame.settings_frame.IsShown())

        push_button(self.frame.settings_frame.close_btn)
        self.assertFalse(self.frame.settings_frame.IsShown())


gui_test_suite = unittest.TestSuite()

gui_test_suite.addTest(
    TestIridaUploaderMain("test_open_sample_sheet"))
gui_test_suite.addTest(
    TestIridaUploaderMain("test_sample_sheet_valid"))
gui_test_suite.addTest(
    TestIridaUploaderMain("test_sample_sheet_multiple_valid"))
gui_test_suite.addTest(
    TestIridaUploaderMain("test_sample_sheet_invalid_no_sheets"))
gui_test_suite.addTest(
    TestIridaUploaderMain("test_sample_sheet_invalid_top_sub_ss"))
'''
gui_test_suite.addTest(
    TestIridaUploaderMain("test_sample_sheet_invalid_seqfiles"))
gui_test_suite.addTest(
    TestIridaUploaderMain("test_sample_sheet_invalid_seqfiles_no_pair"))
gui_test_suite.addTest(
    TestIridaUploaderMain("test_sample_sheet_invalid_seqfiles_odd_len"))
gui_test_suite.addTest(
    TestIridaUploaderMain("test_sample_sheet_invalid_seqfiles_no_project"))
gui_test_suite.addTest(
    TestIridaUploaderMain("test_open_settings"))
'''
if __name__ == "__main__":

    suite_list = []

    suite_list.append(gui_test_suite)
    full_suite = unittest.TestSuite(suite_list)

    runner = unittest.TextTestRunner()
    runner.run(full_suite)
