import wx
import logging
from wx.lib.pubsub import pub

def send_message(message_id, *args, **kwargs):
    app = wx.GetApp()
    if app:
        wx.CallAfter(pub.sendMessage, message_id, *args, **kwargs)
    else:
        pub.sendMessage(message_id, *args, **kwargs)
