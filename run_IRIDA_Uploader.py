#!/usr/bin/env python

import wx
from GUI.iridaUploaderMain import MainFrame

if __name__ == "__main__":
    app = wx.App(False)
    frame = MainFrame()
    frame.Show()
    frame.settings_frame.attempt_connect_to_api()
    app.MainLoop()
