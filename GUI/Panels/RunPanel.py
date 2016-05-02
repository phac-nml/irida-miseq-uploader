import wx
import logging

from wx.lib.pubsub import pub

from SamplePanel import SamplePanel

class RunPanel(wx.Panel):
    """A wx.Panel to show the contents of a SequencingRun.

    This panel is used to show a complete sequencing run.

    Subscriptions:
        run.upload_started_topic: The upload has initiated, the display is
            is updated to show an overall progress bar for the run.
        run.upload_progress_topic: Called for progress updates. Takes one
            argument `progress`, indicating the number of bytes that have been
            sent. The number of bytes that have been sent can be **per-sample**,
            you do not need to calculate the total number of bytes sent overall.
        run.upload_complete_topic: The upload is completed, the display is
            updated to show 100% completion on the progress bars.
    """

    def __init__(self, parent, run, api):
        """Initialize the RunPanel.

        Args:
            parent: The parent Window for this panel.
            run: The sequencing run that should be displayed.
            api: An initialized instance of an API for interacting with IRIDA.
        """
        wx.Panel.__init__(self, parent, style=wx.SUNKEN_BORDER)
        box = wx.StaticBox(self, label=run.sample_sheet_name)

        self._progress_value = 0
        self._last_progress = 0
        # the current overall progress for the run is calculated as a percentage
        # of the total file size of all samples in the run.
        self._progress_max = sum(sample.get_files_size() for sample in run.sample_list)

        self._sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        pub.subscribe(self._upload_started, run.upload_started_topic)
        pub.subscribe(self._handle_progress, run.upload_progress_topic)
        pub.subscribe(self._upload_complete, run.upload_completed_topic)

        for sample in run.sample_list:
            self._sizer.Add(SamplePanel(self, sample, run, api), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=5)

        self.SetSizer(self._sizer)
        self.Layout()

    def _upload_started(self):
        """Update the display when the upload is started.

        This method will add the progress bar and progress text to the display
        when the run.upload_started_topic is received.
        """
        pub.unsubscribe(self._upload_started, self._run.upload_started_topic)
        self.Freeze()
        self._progress = wx.Gauge(self, range=self._progress_max)
        self._progress_text = wx.StaticText(self, label="  0%")
        progress_sizer = wx.BoxSizer(wx.HORIZONTAL)

        progress_sizer.Add(self._progress, proportion=1)
        progress_sizer.Add(self._progress_text, proportion=0)

        self._sizer.Insert(0, progress_sizer, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=5)
        self.Layout()
        # Update our parent sizer so that samples don't get hidden
        self.GetParent().Layout()
        self.Thaw()

    def _upload_complete(self):
        """Update the display when the upload has been completed.

        This method will set the progress bar to it's maximum value and show
        text of 100% when the run.upload_completed_topic is received.
        """
        self.Freeze()
        self._progress.SetValue(self._progress.GetRange())
        self._progress_text.SetLabel("100%")
        self.Layout()
        self.Thaw()

    def _handle_progress(self, progress):
        """Update the display when progress is provided by the API.

        This method will update the progress bar and text to the current progress
        for uploading the run when the run.upload_progress_topic is received.

        Note that the sender **does not** need to send the overall progress for
        the run. It *can*, but it does not need to. Instead, it may send the
        number of bytes sent **per-sample**. The total number of bytes sent is
        calculated by tracking the number of bytes sent the last time this method
        was called and taking the difference. Then we just sum the differences over
        time. When a new sample is starting, the number of reported bytes sent in
        the `progress` variable will be less, so we reset the diff counter to
        start at 0.

        Args:
            progress: the number of bytes sent by the uploader
        """
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
