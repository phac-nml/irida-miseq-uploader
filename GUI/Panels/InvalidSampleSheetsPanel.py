# coding: utf-8
import wx
import logging

from os.path import dirname, basename, sep as separator

from wx.lib.pubsub import pub
from wx.lib.wordwrap import wordwrap

from GUI.SettingsFrame import SettingsFrame
from API.directoryscanner import DirectoryScannerTopics
from API.pubsub import send_message

class InvalidSampleSheetsPanel(wx.Panel):
    """The InvalidSampleSheetsPanel is the container for errors encountered when
    attempting to process sample sheets.

    Subscriptions:
        DirectoryScannerTopics.garbled_sample_sheet: The sample sheet could not
            be processed by the sample sheet processor, so errors should be displayed
            to the client.
        DirectoryScannerTopics.missing_files: The sample sheet refers to files
            that could not be found.
    """
    def __init__(self, parent, sheets_directory):
        """Initalize InvalidSampleSheetsPanel.

        Args:
            parent: the owning Window
            sheets_directory: the parent directory for searching sample sheets. This
                argument is used in the error message that's displayed to the user to
                tell them where to look to fix any issues.
        """
        wx.Panel.__init__(self, parent)

        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self._sizer)
        self._errors_sizer = wx.BoxSizer(wx.VERTICAL)

        header = wx.StaticText(self, label=u"✘ Looks like some sample sheets are not valid.")
        header.SetFont(wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        header.SetForegroundColour(wx.Colour(255, 0, 0))
        header.Wrap(350)

        self._sizer.Add(header,flag=wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER, border=5)
        self._sizer.Add(wx.StaticText(self,
            label=wordwrap((
                "I found the following sample sheets in {}, but I couldn't understand "
                "their contents. Check these sample sheets in an editor outside "
                "of the uploader, then click the 'Scan Again' button below.").format(sheets_directory),
            350, wx.ClientDC(self))), flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=5)
        self._sizer.Add(self._errors_sizer, flag=wx.EXPAND)

        scan_again_button = wx.Button(self, label="Scan Again")
        self.Bind(wx.EVT_BUTTON, lambda evt: send_message(SettingsFrame.connection_details_changed_topic), id=scan_again_button.GetId())
        self._sizer.Add(scan_again_button, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=5)

        pub.subscribe(self._sample_sheet_error, DirectoryScannerTopics.garbled_sample_sheet)
        pub.subscribe(self._sample_sheet_error, DirectoryScannerTopics.missing_files)

    def _sample_sheet_error(self, sample_sheet=None, error=None):
        """Show a list of errors raised during validation of a sample sheet.

        This shows errors that might arise in sample sheet parsing *before* the
        uploader can decide that a sample sheet is a valid run.

        Args:
            sample_sheet: the sample sheet that failed to be parsed.
            error: the error that was raised during validation.
        """
        logging.info("Handling sample sheet error for {}".format(basename(dirname(sample_sheet))))
        self.Freeze()
        box = wx.StaticBox(self, label=basename(dirname(sample_sheet)) + separator + "SampleSheet.csv")
        errors_sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        for err in error.errors:
            error_text = wx.StaticText(self, label=u"• {}".format(err))
            errors_sizer.Add(error_text, flag=wx.LEFT | wx.RIGHT, border=5)
            error_text.Wrap(375)
        self._errors_sizer.Add(errors_sizer, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=3)
        self.GetParent().Layout()
        self.Thaw()
