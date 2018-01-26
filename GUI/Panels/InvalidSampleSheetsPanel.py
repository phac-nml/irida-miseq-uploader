# coding: utf-8
import wx
import logging

from os.path import dirname, basename, sep as separator

from wx.lib.pubsub import pub
from wx.lib.wordwrap import wordwrap

from Exceptions import SampleError, SampleSheetError, SequenceFileError
from API.directoryscanner import DirectoryScannerTopics
from API.pubsub import send_message
from GUI.SettingsDialog import SettingsDialog

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

        self._errors_tree = wx.TreeCtrl(self, style=wx.TR_DEFAULT_STYLE | wx.TR_FULL_ROW_HIGHLIGHT | wx.TR_LINES_AT_ROOT | wx.TR_HIDE_ROOT)
        self._errors_tree_root = self._errors_tree.AddRoot("")
        self._sizer.Add(self._errors_tree, flag=wx.EXPAND, proportion=1)

        scan_again_button = wx.Button(self, label="Scan Again")
        self.Bind(wx.EVT_BUTTON, lambda evt: send_message(SettingsDialog.settings_closed_topic), id=scan_again_button.GetId())
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
        sheet_name = basename(dirname(sample_sheet)) + separator + "SampleSheet.csv"
        logging.info("Handling sample sheet error for {}".format(sheet_name))
        self.Freeze()

        sheet_errors_root = self._errors_tree.AppendItem(self._errors_tree_root, sheet_name)
        sheet_errors_type = None

        if isinstance(error, SampleError):
            sheet_errors_type = self._errors_tree.AppendItem(sheet_errors_root, "Error with Sample Data")
        elif isinstance(error, SequenceFileError):
            sheet_errors_type = self._errors_tree.AppendItem(sheet_errors_root, "Missing FASTQ files")
        elif isinstance(error, SampleSheetError):
            sheet_errors_type = self._errors_tree.AppendItem(sheet_errors_root, "Missing Important Data")

        for err in error.errors:
            self._errors_tree.AppendItem(sheet_errors_type, err.strip())

        self._errors_tree.Expand(sheet_errors_root)

        self.Layout()
        self.GetParent().Layout()
        self.Thaw()
