import wx
import logging

from wx.lib.pubsub import pub

from SamplePanel import SamplePanel

class RunPanel(wx.Panel):
    def __init__(self, parent, run, api):
        wx.Panel.__init__(self, parent, style=wx.SUNKEN_BORDER)
        box = wx.StaticBox(self, label=run.sample_sheet_dir)
        self._progress_value = 0
        self._last_progress = 0
        self._progress_max = sum(sample.get_files_size() for sample in run.sample_list)

        self._sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        self._progress = wx.Gauge(self, range=self._progress_max)
        self._sizer.Add(self._progress, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=5)

        message_id = run.sample_sheet_name + ".upload_progress"
        logging.info("Subscribing to [{}]".format(message_id))
        pub.subscribe(self._handle_progress, message_id)
        pub.subscribe(self._upload_complete, run.sample_sheet_name + ".upload_complete")

        for sample in run.sample_list:
            self._sizer.Add(SamplePanel(self, sample, run, api), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=5)

        self.SetSizer(self._sizer)
        self.Layout()

    def _upload_complete(self):
        self._progress.SetValue(self._progress.GetRange())

    def _handle_progress(self, progress):
        if progress > self._last_progress:
            current_progress = progress - self._last_progress
        else:
            current_progress = 0
        self._last_progress = progress
        self._progress_value += current_progress

        self.Freeze()
        if self._progress_value < self._progress.GetRange():
            self._progress.SetValue(self._progress_value)
        else:
            self._progress.SetValue(self._progress.GetRange())
        self.Thaw()
        #logging.info("Got message for run [{}]".format(progress))
