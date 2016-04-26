import wx
import logging
from wx.lib.pubsub import pub

def send_message(message_id, *args, **kwargs):
    app = wx.GetApp()
    if app:
        logging.info("Sending message to GUI")
        wx.CallAfter(pub.sendMessage, message_id, *args, **kwargs)
    else:
        logging.info("Sending message to command line")
        pub.sendMessage(message_id, *args, **kwargs)
