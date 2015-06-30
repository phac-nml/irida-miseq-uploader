import unittest
import wx
from os import path

from GUI.iridaUploaderMain import MainFrame




class TestIridaUploaderMain(unittest.TestCase):

    def setUp(self):
        print "\nStarting " + self.__module__ + ": " + self._testMethodName
        self.app = wx.App(False)
        self.frame = MainFrame()
        self.WAIT_TIME = 300

    def test_open_sample_sheet(self):

      def _timer_handler(self, evt):

          self.assertTrue(self.frame.dir_dlg.IsShown())
          self.frame.dir_dlg.EndModal(wx.ID_CANCEL)

      #using timer because dir_dlg thread is waiting for user input
      self.frame.timer = wx.Timer(self.frame)
      self.frame.Bind(wx.EVT_TIMER,
                      lambda evt: _timer_handler(self, evt),
                      self.frame.timer)

      self.frame.timer.Start(self.WAIT_TIME, oneShot=True)

      button_evt=wx.PyCommandEvent(wx.EVT_BUTTON.typeId,
                                   self.frame.browse_button.GetId())
      self.frame.browse_button.GetEventHandler().ProcessEvent(button_evt)


gui_test_suite = unittest.TestSuite()

gui_test_suite.addTest(
    TestIridaUploaderMain("test_open_sample_sheet"))
#gui_test_suite.addTest(
    #TestIridaUploaderMain("test_sample_sheet_valid"))
if __name__ == "__main__":

    suite_list = []

    suite_list.append(gui_test_suite)
    full_suite = unittest.TestSuite(suite_list)

    runner = unittest.TextTestRunner()
    runner.run(full_suite)
