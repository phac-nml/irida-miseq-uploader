# coding: utf-8
import wx
import logging
import threading

from wx.lib.pubsub import pub
from Validation import project_exists

class SamplePanel(wx.Panel):
    """A wx.Panel to show an individual Sample.

    This panel is used to show sample-related information and to show upload
    status for an individual sample.

    Subscriptions:
        sample.online_validation_topic: The sample has been validated. Takes one
            argument, the project that the sample sheet indicated, or None.
        sample.upload_started_topic: The upload for this specific sample has
            initiated. The display is updated to show a progress bar for the sample.
        sample.upload_progress_topic: Called for progress updates. Takes one
            argument `progress` with the number of bytes that have been sent to
            the server.
    """

    def __init__(self, parent, sample, run, api):
        """Initialize the SamplePanel.

        Args:
            parent: the parent Window for this panel.
            sample: the sample that should be displayed.
            run: the run that this sample belongs to.
            api: an initialized instance of an API for interacting with IRIDA.
        """
        wx.Panel.__init__(self, parent)
        self._sample = sample

        self._timer = wx.Timer(self)

        self._progress_value = 0
        self._last_timer_progress = 0

        self._progress_max = sample.get_files_size()

        self._sizer = wx.BoxSizer(wx.HORIZONTAL)

        self._label = wx.StaticText(self, label=self._sample.get_id())
        self._sizer.Add(self._label, proportion=2)
        self._status_label = wx.StaticText(self, label="Validating...")
        self._sizer.Add(self._status_label)

        self.SetSizer(self._sizer)

        self.Bind(wx.EVT_TIMER, self._update_progress_timer, self._timer)

        self.Layout()

        pub.subscribe(self._validation_results, sample.online_validation_topic)
        pub.subscribe(self._upload_started, sample.upload_started_topic)
        pub.subscribe(self._upload_completed, sample.upload_completed_topic)
        pub.subscribe(self._upload_progress, sample.upload_progress_topic)

        threading.Thread(target=project_exists, kwargs={"api": api, "project_id": sample.get_project_id(), "message_id": sample.online_validation_topic}).start()

    @property
    def sample(self):
        return self._sample

    def _validation_results(self, project=None):
        """Show the results of the online validation (checking if the project exists).

        Args:
            project: the project (if it exists) or None.
        """

        pub.unsubscribe(self._validation_results, self._sample.online_validation_topic)
        self.Freeze()
        if project:
            self._status_label.SetLabel("{} ({})".format(self._sample.get_project_id(), project.get_name()))
        else:
            self._status_label.SetLabel("Project with ID {} does not exist.".format(self._sample.get_project_id()))
        self.Layout()
        self.Thaw()

    def _upload_started(self):
        """Update the display when the upload is started.

        This method will add the progress bar to the display when the upload
        started topic is recieved.
        """
        logging.info("Upload started for sample {}".format(self._sample.get_id()))
        pub.unsubscribe(self._upload_started, self._sample.upload_started_topic)
        self.Freeze()
        self._status_label.Destroy()
        self._progress = wx.Gauge(self, range=100, size=(100, 20))
        self._sizer.Add(self._progress)
        self.Layout()
        self.Thaw()
        self._timer.Start(1000)

    def _upload_completed(self, sample=None):
        """Stop the timer and hide self when the upload is complete."""

        logging.info("Upload complete for sample {}".format(self._sample.get_id()))

        pub.unsubscribe(self._upload_completed, self._sample.upload_completed_topic)
        pub.unsubscribe(self._upload_progress, self._sample.upload_progress_topic)

        self._timer.Stop()
        self.Freeze()
        complete_label = wx.StaticText(self, label=u"✓")
        complete_label.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        complete_label.SetForegroundColour(wx.Colour(51, 204, 51))
        self._sizer.Add(complete_label, flag=wx.EXPAND | wx.RIGHT, border=5)
        self._progress.Destroy()
        self.Layout()
        self.Thaw()

    def _update_progress_timer(self, event):
        """Update the display when the timer is fired.

        This method is actually responsible for updating the progress bar for the
        sample.

        Arguments:
            event: the event that called this method.
        """
        bytes_sent = self._progress_value - self._last_timer_progress
        logging.info("bytes sent in the last second for {}: [{}, total {}/{}]".format(self._sample.get_id(), bytes_sent, self._progress_value, self._progress_max))

        self.Freeze()
        progress_percent = (self._progress_value / float(self._progress_max)) * 100
        self._progress.SetValue(progress_percent)
        self.Layout()
        self.Thaw()

        self._last_timer_progress = self._progress_value

    def _upload_progress(self, progress):
        """Update the display when progress is provided by the API.

        Args:
            progress: the total number of bytes sent by the API for this sample.
        """
        self._progress_value = progress
