import unittest
import wx
from os import path, listdir

from GUI.iridaUploaderMain import MainFrame


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
        self.WAIT_TIME = 300

    def tearDown(self):
        self.app.Destroy()

    def test_open_sample_sheet(self):

        def handle_dir_dlg(self, evt):

            self.assertTrue(self.frame.dir_dlg.IsShown())
            self.frame.dir_dlg.EndModal(wx.ID_CANCEL)

        # using timer because dir_dlg thread is waiting for user input
        self.frame.timer = wx.Timer(self.frame)
        self.frame.Bind(wx.EVT_TIMER,
                        lambda evt: handle_dir_dlg(self, evt),
                        self.frame.timer)

        self.frame.timer.Start(self.WAIT_TIME, oneShot=True)
        push_button(self.frame.browse_button)

    def test_sample_sheet_valid(self):

        def handle_dir_dlg(self, evt):

            self.assertTrue(self.frame.dir_dlg.IsShown())
            self.frame.dir_dlg.EndModal(wx.ID_OK)
            self.assertFalse(self.frame.dir_dlg.IsShown())

        # using timer because dir_dlg thread is waiting for user input
        self.frame.timer = wx.Timer(self.frame)
        self.frame.browse_path = "./fake_ngs_data/child"
        # dir_dlg uses parent of browse_path; need /child to get /fake_ngs_data

        self.frame.Bind(wx.EVT_TIMER,
                        lambda evt: handle_dir_dlg(self, evt),
                        self.frame.timer)

        self.frame.timer.Start(self.WAIT_TIME, oneShot=True)
        push_button(self.frame.browse_button)

        self.assertIn("SampleSheet.csv is valid",
                      self.frame.log_panel.GetValue())
        self.assertEqual(self.frame.VALID_SAMPLESHEET_BG_COLOR,
                         self.frame.dir_box.GetBackgroundColour())

    def test_sample_sheet_multiple_valid(self):

        def handle_dir_dlg(self, evt):

            self.assertTrue(self.frame.dir_dlg.IsShown())
            self.frame.dir_dlg.EndModal(wx.ID_OK)
            self.assertFalse(self.frame.dir_dlg.IsShown())

        # using timer because dir_dlg thread is waiting for user input
        self.frame.timer = wx.Timer(self.frame)
        self.frame.browse_path = "./testMultiValidSheets/child"

        self.frame.Bind(wx.EVT_TIMER,
                        lambda evt: handle_dir_dlg(self, evt),
                        self.frame.timer)

        self.frame.timer.Start(self.WAIT_TIME, oneShot=True)
        push_button(self.frame.browse_button)

        self.assertEqual(self.frame.log_panel.GetValue().count(
                         "SampleSheet.csv is valid"), 2)
        self.assertEqual(self.frame.VALID_SAMPLESHEET_BG_COLOR,
                         self.frame.dir_box.GetBackgroundColour())

    def test_sample_sheet_invalid_no_sheets(self):

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
            self.assertIn("SampleSheet.csv file not found in the selected " +
                          "directory:\n" + self.frame.browse_path,
                          self.frame.warn_dlg.Message)

            self.frame.warn_dlg.EndModal(wx.ID_OK)
            self.assertFalse(self.frame.warn_dlg.IsShown())

        # using timer because dir_dlg thread is waiting for user input
        self.frame.timer = wx.Timer(self.frame)
        self.frame.browse_path = "./testSampleSheets/child"

        self.frame.Bind(wx.EVT_TIMER,
                        lambda evt: handle_dir_dlg(self, evt),
                        self.frame.timer)
        self.frame.timer.Start(self.WAIT_TIME, oneShot=True)

        push_button(self.frame.browse_button)

        self.assertEqual(self.frame.INVALID_SAMPLESHEET_BG_COLOR,
                         self.frame.dir_box.GetBackgroundColour())

    def test_sample_sheet_invalid_top_sub_ss(self):
        #  samplesheet found in both top of directory and subdirectory

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

            self.assertIn("Found SampleSheet.csv in both top level " +
                          "directory:\n {t_dir}\nand subdirectory".
                          format(t_dir=self.frame.browse_path),
                          self.frame.warn_dlg.Message)

            self.assertIn("You can only have either:\n" +
                          "  One SampleSheet.csv on the top level " +
                          "directory\n  Or multiple SampleSheet.csv " +
                          "files in the the subdirectories",
                          self.frame.warn_dlg.Message)

            self.frame.warn_dlg.EndModal(wx.ID_OK)
            self.assertFalse(self.frame.warn_dlg.IsShown())

        # using timer because dir_dlg thread is waiting for user input
        self.frame.timer = wx.Timer(self.frame)
        self.frame.browse_path = "./testSeqPairFiles/child"

        self.frame.Bind(wx.EVT_TIMER,
                        lambda evt: handle_dir_dlg(self, evt),
                        self.frame.timer)
        self.frame.timer.Start(self.WAIT_TIME, oneShot=True)

        push_button(self.frame.browse_button)

        self.assertEqual(self.frame.INVALID_SAMPLESHEET_BG_COLOR,
                         self.frame.dir_box.GetBackgroundColour())


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

if __name__ == "__main__":

    suite_list = []

    suite_list.append(gui_test_suite)
    full_suite = unittest.TestSuite(suite_list)

    runner = unittest.TextTestRunner()
    runner.run(full_suite)
