# coding: utf-8

import wx

class ProcessingPlaceholderText(wx.StaticText):
    """Displays a spinner until the parent calls either `SetSuccess` or `SetError`."""

    # clock faces through 12 o'clock
    blocks = [u"\U0001F550", u"\U0001F551", u"\U0001F552", u"\U0001F553", u"\U0001F554", u"\U0001F555", u"\U0001F556", u"\U0001F557", u"\U0001F558", u"\U0001F559", u"\U0001F55a", u"\U0001F55b"]

    def __init__(self, parent, *args, **kwargs):
        wx.StaticText.__init__(self, parent, *args, **kwargs)
        self._timer = wx.Timer(self)
        self._current_char = 0

        # this is the only font face on windows that actually renders the clock faces correctly.
        self.SetFont(wx.Font(wx.DEFAULT, wx.DEFAULT, wx.NORMAL, wx.DEFAULT, face="Segoe UI Symbol"))

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
