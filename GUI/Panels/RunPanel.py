import wx
import logging

from wx.lib.pubsub import pub

from SamplePanel import SamplePanel

class RunPanel(wx.Panel):
    def __init__(self, parent, run, api):
        wx.Panel.__init__(self, parent, style=wx.SUNKEN_BORDER)
        box = wx.StaticBox(self, label=run.sample_sheet_name)
        self._progress_value = 0
        self._last_progress = 0
        self._progress_max = sum(sample.get_files_size() for sample in run.sample_list)

        self._sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        message_id = run.sample_sheet_name + ".upload_progress"
        logging.info("Subscribing to [{}]".format(message_id))

        pub.subscribe(self._upload_started, run.sample_sheet_name + ".upload_started")
        pub.subscribe(self._handle_progress, message_id)
        pub.subscribe(self._upload_complete, run.sample_sheet_name + ".upload_complete")

        for sample in run.sample_list:
            self._sizer.Add(SamplePanel(self, sample, run, api), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=5)

        self.SetSizer(self._sizer)
        self.Layout()

    def _upload_started(self):
        self.Freeze()
        self._progress = wx.Gauge(self, range=self._progress_max)
        self._progress_text = wx.StaticText(self, label="  0%")
        progress_sizer = wx.BoxSizer(wx.HORIZONTAL)

        progress_sizer.Add(self._progress, proportion=1)
        progress_sizer.Add(self._progress_text, proportion=0)

        self._sizer.Insert(0, progress_sizer, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=5)
        # Update our parent sizer so that samples don't get hidden
        self.GetParent().Layout()
        self.Layout()
        self.Thaw()

    def _upload_complete(self):
        self.Freeze()
        self._progress.SetValue(self._progress.GetRange())
        self._progress_text.SetLabel("100%")
        self.Layout()
        self.Thaw()

    def _handle_progress(self, progress):
        if progress > self._last_progress:
            current_progress = progress - self._last_progress
        else:
            current_progress = 0
        self._last_progress = progress
        self._progress_value += current_progress

        if self._progress_value < self._progress.GetRange():
            self.Freeze()
            self._progress.SetValue(self._progress_value)
            progress_percent = (self._progress_value / float(self._progress.GetRange())) * 100
            self._progress_text.SetLabel("{:3.0f}%".format(progress_percent))
            self.Layout()
            self.Thaw()
