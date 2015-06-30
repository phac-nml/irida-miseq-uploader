import unittest
import wx
from os import path

from GUI.iridaUploaderMain import MainFrame


class TestIridaUploaderMain(unittest.TestCase):

    def setUp(self):
        print "\nStarting " + self.__module__ + ": " + self._testMethodName
        self.app = wx.App(False)
        self.frame = MainFrame()
        self.WAIT_TIME = 100

    def test_open_sample_sheet(self):

        def _timer_handler(self, evt):

            self.assertTrue(self.frame.dir_dlg.IsShown())
            self.frame.dir_dlg.EndModal(wx.ID_CANCEL)

        # using timer because dir_dlg thread is waiting for user input
        self.frame.timer = wx.Timer(self.frame)
        self.frame.Bind(wx.EVT_TIMER,
                        lambda evt: _timer_handler(self, evt),
                        self.frame.timer)

        self.frame.timer.Start(self.WAIT_TIME, oneShot=True)

        button_evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId,
                                       self.frame.browse_button.GetId())
        self.frame.browse_button.GetEventHandler().ProcessEvent(button_evt)

    def test_sample_sheet_valid(self):

        def _timer_handler(self, evt):

            self.assertTrue(self.frame.dir_dlg.IsShown())
            self.frame.dir_dlg.EndModal(wx.ID_OK)

        # using timer because dir_dlg thread is waiting for user input
        self.frame.timer = wx.Timer(self.frame)
        self.frame.browse_path = "./fake_ngs_data/testSampleSheets"

        self.frame.Bind(wx.EVT_TIMER,
                        lambda evt: _timer_handler(self, evt),
                        self.frame.timer)

        self.frame.timer.Start(self.WAIT_TIME, oneShot=True)

        button_evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId,
                                       self.frame.browse_button.GetId())
        self.frame.browse_button.GetEventHandler().ProcessEvent(button_evt)

        self.assertTrue("Selected SampleSheet is valid" in
                        self.frame.log_panel.GetValue())
        self.assertEqual(self.frame.VALID_SAMPLESHEET_BG_COLOR,
                         self.frame.dir_box.GetBackgroundColour())

gui_test_suite = unittest.TestSuite()

gui_test_suite.addTest(
    TestIridaUploaderMain("test_open_sample_sheet"))
gui_test_suite.addTest(
    TestIridaUploaderMain("test_sample_sheet_valid"))
if __name__ == "__main__":

    suite_list = []

    suite_list.append(gui_test_suite)
    full_suite = unittest.TestSuite(suite_list)

    runner = unittest.TextTestRunner()
    runner.run(full_suite)
