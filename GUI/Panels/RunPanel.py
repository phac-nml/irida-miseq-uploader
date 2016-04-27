import wx
import logging
from SamplePanel import SamplePanel


class RunPanel(wx.Panel):
    def __init__(self, parent, run):
        wx.Panel.__init__(self, parent, style=wx.SUNKEN_BORDER)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        for sample in run.sample_list:
            self.sizer.Add(SamplePanel(self, sample), flag=wx.EXPAND)

        self.SetSizer(self.sizer)
        self.Layout()
