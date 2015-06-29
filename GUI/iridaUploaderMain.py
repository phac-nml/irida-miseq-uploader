import wx
from pprint import pprint
from os import path

from Parsers.miseqParser import (complete_parse_samples, parse_metadata,
                                 get_pair_files)
from Model.SequencingRun import SequencingRun
from Validation.offlineValidation import (validate_sample_sheet,
                                          validate_pair_files,
                                          validate_sample_list)
from Exceptions.SampleSheetError import SampleSheetError
from Exceptions.SequenceFileError import SequenceFileError
from SettingsFrame import SettingsFrame

path_to_module = path.dirname(__file__)
if len(path_to_module) == 0:
    path_to_module = '.'


class MainFrame(wx.Frame):

    def __init__(self, parent=None):

        self.parent = parent
        self.WINDOW_SIZE = (700, 500)
        wx.Frame.__init__(self, parent=self.parent, id=wx.ID_ANY,
                          title="IRIDA Uploader",
                          size=self.WINDOW_SIZE,
                          style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^
                          wx.MAXIMIZE_BOX)

        self.sample_sheet_file = ""
        self.seq_run = None
        self.browse_path = "../"  # os.getcwd()
        self.file_dlg = None
        self.p_bar_percent = 0
        self.base_URL = ""
        self.username = ""
        self.password = ""

        self.LONG_BOX_SIZE = (400, 32)  # url and directories
        self.SHORT_BOX_SIZE = (200, 32)  # user and pass
        self.LABEL_TEXT_WIDTH = 70
        self.LABEL_TEXT_HEIGHT = 32

        self.top_sizer = wx.BoxSizer(wx.VERTICAL)
        self.directory_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.log_panel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.progress_bar_sizer = wx.BoxSizer(wx.VERTICAL)
        self.upload_button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.settings_button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.add_select_sample_sheet_section()
        self.add_log_panel_section()
        self.add_settings_button()
        self.add_progress_bar()
        self.add_upload_button()

        self.top_sizer.AddSpacer(10)  # space between top and directory box

        self.top_sizer.Add(
            self.directory_sizer, proportion=0, flag=wx.ALL, border=5)

        self.top_sizer.AddSpacer(30)  # between directory box & credentials

        self.top_sizer.Add(
            self.log_panel_sizer, proportion=0, flag=wx.ALL | wx.ALIGN_CENTER)

        self.top_sizer.Add(
            self.settings_button_sizer, proportion=0,
            flag=wx.RIGHT | wx.ALIGN_RIGHT, border=15)

        self.top_sizer.AddStretchSpacer()
        self.top_sizer.Add(
            self.progress_bar_sizer, proportion=0,
            flag=wx.ALL | wx.ALIGN_CENTER, border=5)

        self.top_sizer.AddStretchSpacer()
        self.top_sizer.Add(
            self.upload_button_sizer, proportion=0,
            flag=wx.BOTTOM | wx.ALIGN_CENTER, border=5)

        self.SetSizer(self.top_sizer)
        self.Layout()

        self.Bind(wx.EVT_CLOSE, self.close_handler)
        self.settings_frame = SettingsFrame(self)
        self.settings_frame.Hide()
        self.Center()
        self.Show()

    def add_select_sample_sheet_section(self):

        """
        Adds data directory text label, text box and button in to panel
        Sets a tooltip when hovering over text label, text box or button
            describing what file needs to be selected

        Clicking the browse button or the text box launches the file dialog so
            that user can select SampleSheet file

        no return value
        """

        self.dir_label = wx.StaticText(
            parent=self, id=-1,
            size=(self.LABEL_TEXT_WIDTH, self.LABEL_TEXT_HEIGHT),
            label="File path")
        self.dir_box = wx.TextCtrl(self, size=self.LONG_BOX_SIZE)
        self.browse_button = wx.Button(self, label="Choose directory")
        self.browse_button.SetFocus()

        self.directory_sizer.Add(self.dir_label, 0, wx.ALL, 5)
        self.directory_sizer.Add(self.dir_box, 0, wx.ALL, 5)
        self.directory_sizer.Add(self.browse_button, 0, wx.ALL, 5)

        tip = "Select the directory containing the SampleSheet.csv file " + \
            "to be uploaded"
        self.dir_box.SetToolTipString(tip)
        self.dir_label.SetToolTipString(tip)
        self.browse_button.SetToolTipString(tip)

        self.Bind(wx.EVT_BUTTON, self.open_dir_dlg, self.browse_button)
        # clicking directoryBox
        self.dir_box.Bind(wx.EVT_LEFT_DOWN, self.open_dir_dlg)
        # tabbing in to directorybox
        self.dir_box.Bind(wx.EVT_SET_FOCUS, self.open_dir_dlg)

    def add_progress_bar(self):

        """
        Adds progress bar. Will be used for displaying progress of
            sequence files upload.

        no return value
        """

        self.progress_label = wx.StaticText(
            self, id=-1, size=(self.LABEL_TEXT_WIDTH, self.LABEL_TEXT_HEIGHT),
            label=str(self.p_bar_percent) + "%")
        self.progress_bar = wx.Gauge(self, range=100, size=(
            self.WINDOW_SIZE[0] * 0.95, self.LABEL_TEXT_HEIGHT))
        self.progress_bar_sizer.Add(self.progress_label)
        self.progress_bar_sizer.Add(self.progress_bar)
        self.progress_label.Hide()
        self.progress_bar.Hide()

    def add_upload_button(self):

        """
        Adds upload button to panel

        no return value
        """

        self.upload_button = wx.Button(self, label="Upload")
        self.upload_button.Disable()

        self.upload_button_sizer.Add(self.upload_button)
        self.Bind(wx.EVT_BUTTON, self.upload_to_server, self.upload_button)

        tip = "Upload sequence files to IRIDA server. " + \
            "Select a valid SampleSheet file to enable button."
        self.upload_button.SetToolTipString(tip)

    def add_log_panel_section(self):

        """
        Adds log panel text control for displaying progress and errors

        no return value
        """

        self.log_panel = wx.TextCtrl(
            self, id=-1,
            value="Waiting for user to select directory containing " +
                  "SampleSheet file.\n\n",
            size=(self.WINDOW_SIZE[0]*0.95, 200),
            style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.log_panel_sizer.Add(self.log_panel)

    def open_settings(self, evt):

        """
        Open the settings menu(SettingsFrame)

        no return value
        """

        self.settings_frame.Center()
        self.settings_frame.Show()

    def add_settings_button(self):

        """
        Adds settings button to open settings menu

        no return value
        """

        self.settings_button = wx.Button(self, label="Settings")
        self.settings_button.Bind(wx.EVT_BUTTON, self.open_settings)
        self.settings_button_sizer.Add(self.settings_button)

    def display_warning(self, warn_msg):

        """Displays warning message

        arguments:
                warn_msg -- message to display in warning dialog message box

        no return value
        """

        self.log_panel.AppendText(warn_msg + "\n")
        warn_dlg = wx.MessageDialog(
            parent=self, message=warn_msg, caption="Warning!",
            style=wx.OK | wx.ICON_WARNING)
        warn_dlg.ShowModal()
        warn_dlg.Destroy()

    def close_handler(self, event):

        """
        Function bound to window/MainFrame being closed (close button/alt+f4)
        Destroy SettingsFrame and then destroy self

        no return value
        """
        self.settings_frame.Destroy()
        self.Destroy()

    def upload_to_server(self, event):

        """
        Function bound to upload_button being clicked
        Currently just prints values entered in text boxes
            and pairFiles in seqRun

        arguments:
                event -- EVT_BUTTON when upload button is clicked

        no return value
        """

        print("Server URL: " + self.base_URL + "\n" + "User: " +
              self.username + "\n" + "Password: " +
              self.password.strip())
        self.p_bar_percent += 1
        self.progress_label.SetLabel(str(self.p_bar_percent) + "%")
        self.progress_bar.SetValue(self.p_bar_percent)

        if self.seq_run is not None:
            print self.seq_run.get_workflow()
            pprint([self.seq_run.get_pair_files(sample.get_id())
                    for sample in self.seq_run.get_sample_list()])

    def handle_invalid_sheet_or_seq_file(self, msg):

        """
        disable GUI elements and reset variables when an error happens

        displays warning message for the given msg
        disables upload button - greyed out and unclickable
        progress bar and label are hidden
        progress bar percent counter is reset back to 0
        self.seq_run set to None

        arguments:
                msg -- message to display in warning dialog message box

        no return value
        """

        self.display_warning(msg)
        self.upload_button.Disable()
        self.dir_box.SetValue("")
        self.progress_label.Hide()
        self.progress_bar.Hide()
        self.p_bar_percent = 0
        self.progress_label.SetLabel(str(self.p_bar_percent) + "%")
        self.progress_bar.SetValue(self.p_bar_percent)
        self.seq_run = None

    def open_dir_dlg(self, event):

        """
        Function bound to browseButton being clicked and directoryBox being
            clicked or tabbbed/focused
        Opens file dialog for user to select SampleSheet.csv
        Validates the selected SampleSheet
        If it's valid then proceed to create the sequence run (create_seq_run)
        else displays warning messagebox containing the error(s)

        arguments:
            event -- EVT_BUTTON when browse button is clicked
                    or EVT_SET_FOCUS when directoryBox is focused via tabbing
                    or EVT_LEFT_DOWN when directoryBox is clicked

        no return value
        """

        self.browse_button.SetFocus()

        self.file_dlg = wx.FileDialog(
            self, "Select SampleSheet.csv file",  defaultDir=self.browse_path,
            style=wx.DD_DEFAULT_STYLE)

        if self.file_dlg.ShowModal() == wx.ID_OK:

            self.browse_path = self.file_dlg.GetDirectory()

            try:
                v_res = validate_sample_sheet(self.file_dlg.GetPath())

                if v_res.is_valid():
                    self.sample_sheet_file = self.file_dlg.GetPath()

                    try:
                        self.create_seq_run()
                        self.dir_box.SetValue(self.sample_sheet_file)
                        self.upload_button.Enable()
                        self.log_panel.AppendText(
                            "Selected SampleSheet is valid\n")
                        self.progress_label.Show()
                        self.progress_bar.Show()
                        self.Layout()

                    except (SampleSheetError, SequenceFileError), e:
                        self.handle_invalid_sheet_or_seq_file(str(e))

                else:
                    self.handle_invalid_sheet_or_seq_file(v_res.get_errors())

            except SampleSheetError, e:
                self.handle_invalid_sheet_or_seq_file(str(e))

        self.file_dlg.Destroy()

    def create_seq_run(self):

        """
        Try to create a SequencingRun object and store in to self.seq_run
        Parses out the metadata dictionary and sampleslist from selected
            self.sample_sheet_file
        raises errors:
                if parsing raises/throws Exceptions
                if the parsed out samplesList fails validation
                if a pair file for a sample in samplesList fails validation
        these errors are expected to be caught by the calling function
            open_dir_dlg and it will be the one sending them to display_warning

        no return value
        """

        try:
            m_dict = parse_metadata(self.sample_sheet_file)
            s_list = complete_parse_samples(self.sample_sheet_file)

        except SequenceFileError, e:
            raise SequenceFileError(str(e))

        except SampleSheetError, e:
            raise SampleSheetError(str(e))

        v_res = validate_sample_list(s_list)
        if v_res.is_valid():

            self.seq_run = SequencingRun()
            self.seq_run.set_metadata(m_dict)
            self.seq_run.set_sample_list(s_list)

        else:
            raise SequenceFileError(v_res.get_errors())

        for sample in self.seq_run.get_sample_list():
            pf_list = self.seq_run.get_pair_files(sample.get_id())

            v_res = validate_pair_files(pf_list)
            if v_res.is_valid() is False:
                raise SequenceFileError(v_res.get_errors())


if __name__ == "__main__":
    app = wx.App(False)
    frame = MainFrame()
    frame.Show()
    frame.settings_frame.attempt_connect_to_api()
    app.MainLoop()
