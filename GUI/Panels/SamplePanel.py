import wx
import logging

class SamplePanel(wx.Panel):

    def __init__(self, parent, sample):
        wx.Panel.__init__(self, parent)
        self._sample = sample
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)

        self._checkbox = wx.CheckBox(self, label=self._sample.get_id(), style=wx.CHK_3STATE|wx.CHK_ALLOW_3RD_STATE_FOR_USER)

        self.sizer.Add(self._checkbox, proportion=2)

        self.sizer.Add(wx.StaticText(self, label="298 / 399MB"))
        self._gauge = wx.Gauge(self, range=100)
        self._gauge.SetValue(75)
        self.sizer.Add(self._gauge)
        self.SetSizer(self.sizer)
        self.Layout()
