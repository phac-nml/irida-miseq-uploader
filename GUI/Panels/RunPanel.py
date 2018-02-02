# coding: utf-8
import wx
import logging

from wx.lib.pubsub import pub
from wx.lib.scrolledpanel import ScrolledPanel

from SamplePanel import SamplePanel

class RunPanel(ScrolledPanel):
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
        ScrolledPanel.__init__(self, parent, style=wx.SUNKEN_BORDER)
        box = wx.StaticBox(self, label=run.sample_sheet_name)
        self._timer = wx.Timer(self)

        self._run = run

        self._progress_value = 0
        self._last_progress = 0
        self._last_timer_progress = 0
        self._sample_panels = {}
        self._progress = wx.Gauge(self, id=wx.ID_ANY, range=100, size=(250, 20))
        self._progress.Hide()
        self._progress_text = wx.StaticText(self, label="  0%")
        self._progress_text.Hide()
        # the current overall progress for the run is calculated as a percentage
        # of the total file size of all samples in the run.
        self._progress_max = sum(sample.get_files_size() for sample in run.samples_to_upload)
        logging.info("Total file size for run is {}".format(self._progress_max))

        self._sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        pub.subscribe(self._upload_started, run.upload_started_topic)
        pub.subscribe(self._handle_progress, run.upload_progress_topic)
        pub.subscribe(self._upload_complete, run.upload_completed_topic)
        pub.subscribe(self._upload_failed, run.upload_failed_topic)

        for sample in run.sample_list:
            self._sample_panels[sample.get_id()] = SamplePanel(self, sample, run, api)
            self._sizer.Add(self._sample_panels[sample.get_id()], flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=5)

        self.SetSizer(self._sizer)
        self.Bind(wx.EVT_TIMER, self._update_progress_timer, self._timer)
        self.Layout()
        self.SetupScrolling()

    def _update_progress_timer(self, event):
        """Update the display when the timer is fired.

        This method is actually responsible for updating the progress bar for the
        run, and maintains the current upload speed for the run.

        Arguments:
            event: the event that called this method.
        """
        bytes_sent = self._progress_value - self._last_timer_progress

        logging.info("bytes sent in last second: [{}]".format(bytes_sent))
        speed = "0 KB/s"
        if bytes_sent > 1000000:
            speed = "{:2.0f} MB/s".format(bytes_sent/1000000.0)
        else:
            speed = "{} KB/s".format(bytes_sent/1000)


        if self._progress_value < self._progress_max:
            self.Freeze()
            progress_percent = (self._progress_value / float(self._progress_max)) * 100
            self._progress.SetValue(progress_percent)
            self._progress_text.SetLabel("{:3.0f}% {}".format(progress_percent, speed))
            self.Layout()
            self.Thaw()

        self._last_timer_progress = self._progress_value

    def _upload_started(self):
        """Update the display when the upload is started.

        This method will add the progress bar and progress text to the display
        when the run.upload_started_topic is received.
        """
        logging.info("Upload started for {} with max size {}".format(self._run.upload_started_topic, self._progress_max))
        pub.unsubscribe(self._upload_started, self._run.upload_started_topic)
        self.Freeze()
        progress_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._progress.Show()
        progress_sizer.Add(self._progress, proportion=1)
        self._progress_text.Show()
        progress_sizer.Add(self._progress_text, proportion=0)

        self._sizer.Insert(0, progress_sizer, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=5)
        self.Layout()
        # Update our parent sizer so that samples don't get hidden
        self.GetParent().Layout()
        self.Thaw()
        self._timer.Start(1000)

    def _upload_failed(self, exception=None):
        """Update the display when the upload has failed.

        Args:
            exception: the exception that caused the failure.
        """

        pub.unsubscribe(self._upload_failed, self._run.upload_failed_topic)
        pub.unsubscribe(self._handle_progress, self._run.upload_progress_topic)
        pub.unsubscribe(self._upload_complete, self._run.upload_completed_topic)
        
        self.Freeze()
        if self._timer.IsRunning():
            self._timer.Stop()
        self._progress_text.Hide()
        self._progress.Hide()
        error_label = wx.StaticText(self, label=u"✘ Yikes!")
        error_label.SetForegroundColour(wx.Colour(255, 0, 0))
        error_label.SetFont(wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        detailed_error_label = wx.StaticText(self, label="The IRIDA server failed to accept the upload. You can try again by clicking the 'Try again' button below. If the problem persists, please contact an IRIDA administrator.".format(str(exception)))
        detailed_error_label.Wrap(350)

        self._sizer.Insert(0, detailed_error_label, flag=wx.EXPAND | wx.ALL, border=5)
        self._sizer.Insert(0, error_label, flag=wx.EXPAND | wx.ALL, border=5)

        self.Layout()
        self.Thaw()

    def _upload_complete(self, sample=None):
        """Update the display when the upload has been completed.

        This method will set the progress bar to it's maximum value and show
        text of 100% when the run.upload_completed_topic is received.
        """
        if sample:
            logging.info("Upload completed for sample {}".format(sample.get_id()))
            sample_panel = self._sample_panels[sample.get_id()]

            # Move the completed sample to the bottom of the list.
            sample_panel.HideWithEffect(wx.SHOW_EFFECT_BLEND)
            self._sizer.Detach(sample_panel)
            self._sizer.Add(sample_panel, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=5)
            sample_panel.ShowWithEffect(wx.SHOW_EFFECT_BLEND)
            self.Layout()
        else:
            logging.info("Upload completed for run {}".format(self._run.upload_started_topic))
            pub.unsubscribe(self._handle_progress, self._run.upload_progress_topic)
            pub.unsubscribe(self._upload_complete, self._run.upload_completed_topic)

            self.Freeze()
            self._progress.SetValue(self._progress.GetRange())
            self._progress_text.SetLabel("100%")
            self._timer.Stop()
            self.Layout()
            self.Thaw()

    def _handle_progress(self, progress):
        """Update the number of bytes sent provided by the API.

        This method will update the number of bytes sent for the current progress
        of uploading the run when the run.upload_progress_topic is received.

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
