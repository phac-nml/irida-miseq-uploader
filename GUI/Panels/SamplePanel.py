import wx
import logging
import threading

from wx.lib.pubsub import pub
from Validation import project_exists

class SamplePanel(wx.Panel):

    def __init__(self, parent, sample, api):
        wx.Panel.__init__(self, parent)
        self._sample = sample
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)

        self._label = wx.StaticText(self, label=self._sample.get_id())
        self.sizer.Add(self._label, proportion=2)
        self._status_label = wx.StaticText(self, label="Validating...")
        self.sizer.Add(self._status_label)

        self.SetSizer(self.sizer)
        self.Layout()

        message_id = "validation_result_" + sample.get_id()
        pub.subscribe(self._validation_results, message_id)
        threading.Thread(target=project_exists, kwargs={"api": api, "project_id": sample.get_project_id(), "message_id": message_id}).start()

    def _validation_results(self, project=None):
        self.Freeze()
        if project:
            self._status_label.SetLabel(project.get_name())
        else:
            self._status_label.SetLabel("Project with ID {} does not exist.".format(self._sample.get_project_id()))
        self.Layout()
        self.Thaw()
