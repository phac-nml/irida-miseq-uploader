import wx
import logging
from SamplePanel import SamplePanel

class RunPanel(wx.Panel):
    def __init__(self, parent, run, api):
        wx.Panel.__init__(self, parent, style=wx.SUNKEN_BORDER)
        box = wx.StaticBox(self, label=run.sample_sheet_dir)
        self._sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        for sample in run.sample_list:
            self._sizer.Add(SamplePanel(self, sample, api), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=5)

        self.SetSizer(self._sizer)
        self.Layout()
