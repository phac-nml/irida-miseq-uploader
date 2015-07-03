import  wx

class IridaMsgBox(wx.Dialog):
    def __init__(self, parent, message="", title="Message Box"):
        """Constructor"""
        DLG_SIZE = (400, 150)
        wx.Dialog.__init__(self, parent, title=title, size=DLG_SIZE,
                           style=wx.DEFAULT_DIALOG_STYLE)

        msg_label = wx.StaticText(self, id=-1, label=message)
        msg_label.Wrap(width=300)

        ok_button = wx.Button(self, wx.ID_OK)

        top_sizer = wx.BoxSizer(wx.VERTICAL)
        msg_sizer = wx.BoxSizer(wx.VERTICAL)
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)


        top_sizer.AddStretchSpacer()
        msg_sizer.Add(msg_label)
        top_sizer.Add(msg_sizer, flag=wx.ALIGN_CENTER)

        top_sizer.AddStretchSpacer()
        btn_sizer.Add(ok_button, flag=wx.ALL, border=5)
        top_sizer.Add(btn_sizer, flag=wx.ALIGN_BOTTOM | wx.ALIGN_RIGHT)


        self.Center()
        self.SetSizer(top_sizer)
        self.Layout()





if __name__ == "__main__":
    app = wx.App()
    frame = wx.Frame(parent=None)
    frame.Center()
    frame.Show()

    imb = IridaMsgBox(frame, "Test "*10, "Title")
    imb.ShowModal()

    app.MainLoop()
