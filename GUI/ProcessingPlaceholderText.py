# coding: utf-8

import wx

class ProcessingPlaceholderText(wx.StaticText):
    """Displays a spinner until the parent calls either `SetSuccess` or `SetError`."""

    blocks = [u"▖", u"▘", u"▝", u"▗"]

    def __init__(self, parent, *args, **kwargs):
        wx.StaticText.__init__(self, parent, *args, **kwargs)
        self._timer = wx.Timer(self)
        self._current_char = 0

        self.SetFont(wx.Font(wx.DEFAULT, wx.DEFAULT, wx.NORMAL, wx.BOLD))

        self.Bind(wx.EVT_TIMER, self._update_progress_text, self._timer)
        self.Restart()

    def _update_progress_text(self, evt=None):
        super(ProcessingPlaceholderText, self).SetLabel(ProcessingPlaceholderText.blocks[self._current_char % len(ProcessingPlaceholderText.blocks)])
        self._current_char += 1

    def SetError(self, error_message=None):
        self._timer.Stop()
        super(ProcessingPlaceholderText, self).SetLabel(u"✘")
        self.SetToolTipString(error_message)
        self.SetForegroundColour(wx.Colour(255, 0, 0))

    def SetSuccess(self, api=None):
        self._timer.Stop()
        super(ProcessingPlaceholderText, self).SetLabel(u"✓")
        self.SetForegroundColour(wx.Colour(51, 204, 51))

    def Restart(self):
        self.SetForegroundColour(wx.Colour(0, 0, 255))
        self._update_progress_text()
        self._timer.Start(500)
