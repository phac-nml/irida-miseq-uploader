import wx
from iridaUploader.GUI.iridaUploaderMain import MainFrame

if __name__ == "__main__":
    app = wx.App(False)
    frame = MainFrame()
    frame.Show()
    frame.mp.api = frame.settings_frame.attempt_connect_to_api()
    app.MainLoop()
