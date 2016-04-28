import wx
import logging
import threading

from wx.lib.pubsub import pub
from Validation import project_exists

class SamplePanel(wx.Panel):

    def __init__(self, parent, sample, run, api):
        wx.Panel.__init__(self, parent)
        self._sample = sample
        self._sizer = wx.BoxSizer(wx.HORIZONTAL)

        self._label = wx.StaticText(self, label=self._sample.get_id())
        self._sizer.Add(self._label, proportion=2)
        self._status_label = wx.StaticText(self, label="Validating...")
        self._sizer.Add(self._status_label)

        self.SetSizer(self._sizer)
        self.Layout()

        message_id = "validation_result_" + sample.get_id()
        progress_message_id = run.sample_sheet_name + ".upload_progress." + sample.get_id()
        sample.progress_message_id = progress_message_id
        logging.info("Progress for sample subscription [{}]".format(progress_message_id))
        pub.subscribe(self._validation_results, message_id)
        pub.subscribe(self._upload_started, "upload_started_" + sample.get_id())
        pub.subscribe(self._upload_progress, progress_message_id)
        threading.Thread(target=project_exists, kwargs={"api": api, "project_id": sample.get_project_id(), "message_id": message_id}).start()

    def _validation_results(self, project=None):
        self.Freeze()
        if project:
            self._status_label.SetLabel(project.get_name())
        else:
            self._status_label.SetLabel("Project with ID {} does not exist.".format(self._sample.get_project_id()))
        self.Layout()
        self.Thaw()

    def _upload_started(self):
        logging.info("Upload started for sample {}".format(self._sample.get_id()))
        self.Freeze()
        self._status_label.Destroy()
        self._progress = wx.Gauge(self, range=self._sample.get_files_size())
        self._sizer.Add(self._progress)
        self.Layout()
        self.Thaw()

    def _upload_progress(self, progress):
        self.Freeze()
        if progress < self._progress.GetRange():
            self._progress.SetValue(progress)
        else:
            self._progress.SetValue(self._progress.GetRange())
        self.Layout()
        self.Thaw()
