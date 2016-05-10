# coding: utf8
import wx
import logging

from wx.lib.pubsub import pub
from wx.lib.wordwrap import wordwrap

from API.directoryscanner import DirectoryScannerTopics

class InvalidSampleSheetsPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self._sizer)

        header = wx.StaticText(self, label=u"✘ Oops! Some of your sample sheets are not valid.")
        header.SetFont(wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        header.SetForegroundColour(wx.Colour(255, 0, 0))
        header.Wrap(350)

        self._sizer.Add(header,flag=wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER, border=5)
        self._sizer.Add(wx.StaticText(self,
            label=wordwrap((
                "I found the following sample sheets, but I couldn't understand "
                "their contents. Check these sample sheets in an editor outside "
                "of the uploader, then click the 'Scan Again' button below."),
            350, wx.ClientDC(self))), flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=5)

        pub.subscribe(self._sample_sheet_error, DirectoryScannerTopics.garbled_sample_sheet)

    def _sample_sheet_error(self, sample_sheet=None, error=None):
        logging.info("Handling sample sheet error for {}".format(sample_sheet))
