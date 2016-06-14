import wx
import json
import sys
from wx.lib.newevent import NewEvent
from os import path, makedirs
from ConfigParser import RawConfigParser
from appdirs import user_config_dir
from wx.lib.pubsub import pub
from GUI.SettingsFrame import SettingsFrame, ConnectionError
from wx.lib.agw.genericmessagedialog import GenericMessageDialog as GMD
from API.directoryscanner import *
from API.runuploader import *
from API.pubsub import send_message
from threading import Thread
from time import time
from math import ceil

path_to_module = path.dirname(__file__)
user_config_dir = user_config_dir("iridaUploader")
user_config_file = path.join(user_config_dir, "config.conf")

if len(path_to_module) == 0:
    path_to_module = '.'

def check_config_dirs(conf_parser):
    """
    Checks to see if the config directories are set up for this user. Will
    create the user config directory and copy a default config file if they
    do not exist

    no return value
    """

    if not path.exists(user_config_dir):
        print "User config dir doesn't exist, making new one."
        makedirs(user_config_dir)

    if not path.exists(user_config_file):
        # find the default config dir from (at least) two directory levels
        # above this directory
        defaults = {
            "baseURL": "http://localhost:8080/api/",
            "username": "admin",
            "password": "password1",
            "client_id": "testClient",
            "client_secret": "testClientSecret"
        }

        for key in defaults.keys():
            conf_parser.set("Settings", key, defaults[key])

        conf_parser.read(conf_file)

class MainPanel(wx.Panel):

    def __init__(self, parent):

        self.parent = parent
        self.WINDOW_SIZE = self.parent.WINDOW_SIZE
        wx.Panel.__init__(self, parent)

        self.send_seq_files_evt, self.EVT_SEND_SEQ_FILES = NewEvent()

        self.conf_parser = RawConfigParser()
        self.config_file = user_config_file
        check_config_dirs(self.conf_parser)
        self.conf_parser.read(self.config_file)

        self.seq_run_list = []

        self.dir_dlg = None
        self.api = None
        self.upload_complete = None
        self.curr_upload_id = None
        self.loaded_upload_id = None
        self.prev_uploaded_samples = []

        self.LABEL_TEXT_WIDTH = 80
        self.LABEL_TEXT_HEIGHT = 32
        self.CF_LABEL_TEXT_HEIGHT = 64
        self.VALID_SAMPLESHEET_BG_COLOR = wx.GREEN
        self.INVALID_SAMPLESHEET_BG_COLOR = wx.RED
        self.LOG_PNL_REG_TXT_COLOR = wx.BLACK
        self.LOG_PNL_ERR_TXT_COLOR = wx.RED
        self.LOG_PNL_OK_TXT_COLOR = (0, 102, 0)  # dark green
        self.PADDING_LEN = 20
        self.SECTION_SPACE = 20
        self.TEXTBOX_FONT = wx.Font(
            pointSize=10, family=wx.FONTFAMILY_DEFAULT,
            style=wx.FONTSTYLE_NORMAL, weight=wx.FONTWEIGHT_NORMAL)
        self.LABEL_TXT_FONT = self.TEXTBOX_FONT

        self.padding = wx.BoxSizer(wx.VERTICAL)
        self.top_sizer = wx.BoxSizer(wx.VERTICAL)
        self.directory_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.cf_label_container = wx.BoxSizer(wx.HORIZONTAL)
        self.log_panel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.ov_label_container = wx.BoxSizer(wx.HORIZONTAL)
        self.ov_upload_est_time_container = wx.BoxSizer(wx.VERTICAL)
        self.progress_bar_sizer = wx.BoxSizer(wx.VERTICAL)
        self.upload_button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.status_icon = wx.StaticBitmap(self, bitmap=wx.EmptyBitmap(24, 24))
        self.warning_icon = wx.Image(path.join(path_to_module, 'images', 'Warning.png'), wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        self.success_icon = wx.Image(path.join(path_to_module, 'images', 'Success.png'), wx.BITMAP_TYPE_ANY).ConvertToBitmap()

        self.add_select_sample_sheet_section()
        self.add_log_panel_section()
        self.add_curr_file_progress_bar()
        self.add_overall_progress_bar()
        self.add_upload_button()

        self.top_sizer.Add(
            self.directory_sizer, proportion=0, flag=wx.ALIGN_CENTER |
            wx.EXPAND)

        self.top_sizer.AddSpacer(self.SECTION_SPACE)
        # between directory box & credentials

        self.top_sizer.Add(
            self.log_panel_sizer, proportion=1, flag=wx.EXPAND |
            wx.ALIGN_CENTER)

        self.top_sizer.Add(
            self.progress_bar_sizer,
            flag=wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER | wx.EXPAND, border=5)

        self.padding.Add(
            self.top_sizer, proportion=1, flag=wx.ALL | wx.EXPAND,
            border=self.PADDING_LEN)

        self.padding.Add(
            self.upload_button_sizer, proportion=0,
            flag=wx.BOTTOM | wx.ALIGN_CENTER, border=self.PADDING_LEN)

        self.SetSizer(self.padding)
        self.Layout()

        # Updates boths progress bars and progress labels
        pub.subscribe(self.update_progress_bars, "update_progress_bars")

        # publisher sends a message that uploading sequence files is complete
        # basically places a call to self.update_progress_bars in the event q
        pub.subscribe(self.seq_files_upload_complete,
                      "seq_files_upload_complete")

        # Called by an api function
        # display error message and update sequencing run uploadStatus to ERROR
        pub.subscribe(self.handle_api_thread_error,
                      "handle_api_thread_error")

        # update self.api when Settings is closed
        # if it's not None (i.e can connect to API) enable the submit button
        pub.subscribe(self.set_updated_api,
                      SettingsFrame.connection_details_changed_topic)

        # Updates upload speed and estimated remaining time labels
        pub.subscribe(self.update_remaining_time, "update_remaining_time")

        # displays the completion command message in to the log panel
        pub.subscribe(self.display_completion_cmd_msg,
                      "display_completion_cmd_msg")

        self.Bind(self.EVT_SEND_SEQ_FILES, self.handle_send_seq_evt)
        self.Bind(wx.EVT_DIRPICKER_CHANGED, self.start_sample_sheet_processing)
        self.settings_frame = SettingsFrame(self)
        self.settings_frame.Hide()
        self.Center()
        self.Show()
	# auto-scan the currently selected directory (which should be the directory
	# that's set in the preferences file).
        self.start_sample_sheet_processing()

    def get_config_default_dir(self):

        """
        Check if the config has a default_dir.  If not set to
        the user's home directory.

        return the path to the default directory from the config file
        """

        default_dir_path = self.conf_parser.get("Settings", "default_dir")

        # if the path is not set, set to home directory
        if not default_dir_path:

            default_dir_path = path.expanduser("~")

        return default_dir_path

    def handle_send_seq_evt(self, evt):

        """
        function bound to custom event self.EVT_SEND_SEQ_FILES
        creates new thread for sending sequence files

        no return value
        """

        kwargs = {
            "samples_list": evt.sample_list,
            "callback": evt.send_callback,
            "upload_id": evt.curr_upload_id,
            "prev_uploaded_samples": evt.prev_uploaded_samples,
        }
        self.api.send_sequence_files(**kwargs)

    def add_select_sample_sheet_section(self):

        """
        Adds data directory text label, text box and button in to panel
        Sets a tooltip when hovering over text label, text box or button
            describing what file needs to be selected

        Clicking the browse button or the text box launches the file dialog so
            that user can select SampleSheet file

        no return value
        """

        self.browse_button = wx.DirPickerCtrl(self,
                                              path=self.get_config_default_dir())
        self.dir_label = wx.StaticText(parent=self, id=-1, label="File path")
        self.dir_label.SetFont(self.LABEL_TXT_FONT)

        self.directory_sizer.Add(self.dir_label, flag=wx.ALIGN_CENTER_VERTICAL)
        self.directory_sizer.Add(self.browse_button, proportion=1, flag=wx.EXPAND)
        self.directory_sizer.Add(self.status_icon, flag=wx.ALIGN_CENTER_VERTICAL)

        tip = "Select the directory containing the SampleSheet.csv file " + \
            "to be uploaded"
        self.dir_label.SetToolTipString(tip)
        self.browse_button.SetToolTipString(tip)

    def add_curr_file_progress_bar(self):

        """
        Adds current file progress bar. Will be used for displaying progress of
            the current sequence files being uploaded.

        no return value
        """

        self.cf_init_label = "\n\nFile: 0%"
        self.cf_progress_label = wx.StaticText(
            self, id=-1,
            label=self.cf_init_label)
        self.cf_progress_label.SetFont(self.LABEL_TXT_FONT)
        self.cf_label_container.SetMinSize(wx.Size(-1,self.CF_LABEL_TEXT_HEIGHT))
        self.cf_label_container.Add(self.cf_progress_label, flag=wx.ALIGN_BOTTOM)
        self.cf_progress_bar = wx.Gauge(self, range=100,
                                        size=(-1, self.LABEL_TEXT_HEIGHT))
        self.progress_bar_sizer.Add(self.cf_label_container, flag=wx.ALIGN_BOTTOM|wx.ALL)
        self.progress_bar_sizer.Add(self.cf_progress_bar, proportion=0,
                                    flag=wx.ALL|wx.EXPAND)
        self.cf_progress_label.Hide()
        self.cf_progress_bar.Hide()

    def add_overall_progress_bar(self):

        """
        Adds overall progress bar. Will be used for displaying progress of
            all sequence files uploaded.

        no return value
        """

        self.ov_init_label = "\nOverall: 0%"
        self.ov_upload_label_text = "Average upload speed: {speed}"
        self.ov_est_time_label_text = "Estimated time remaining: {time}"

        self.ov_progress_label = wx.StaticText(
            self, id=-1,
            label=self.ov_init_label)

        self.ov_upload_label = wx.StaticText(
            self, id=-1,
            label=self.ov_upload_label_text.format(speed="..."),
            style=wx.ALIGN_RIGHT)

        self.ov_est_time_label = wx.StaticText(
            self, id=-1,
            label=self.ov_est_time_label_text.format(time="..."),
            style=wx.ALIGN_RIGHT)

        self.ov_progress_label.SetFont(self.LABEL_TXT_FONT)
        self.ov_upload_label.SetFont(self.LABEL_TXT_FONT)
        self.ov_est_time_label.SetFont(self.LABEL_TXT_FONT)

        self.ov_progress_bar = wx.Gauge(self, range=100,
                                        size=(-1, self.LABEL_TEXT_HEIGHT))

        self.ov_label_container.Add(self.ov_progress_label, flag=wx.ALL|wx.ALIGN_BOTTOM)
        self.ov_label_container.AddStretchSpacer()

        self.ov_upload_est_time_container.Add(self.ov_upload_label, flag=wx.ALL|wx.ALIGN_RIGHT)
        self.ov_upload_est_time_container.Add(self.ov_est_time_label, flag=wx.ALL|wx.ALIGN_RIGHT)
        self.ov_label_container.Add(self.ov_upload_est_time_container, proportion=1,
                                    flag=wx.ALIGN_RIGHT|wx.EXPAND|wx.RIGHT)
        self.progress_bar_sizer.AddSpacer(self.SECTION_SPACE)
        self.progress_bar_sizer.Add(self.ov_label_container, flag=wx.EXPAND)
        self.progress_bar_sizer.Add(self.ov_progress_bar, proportion=0,
                                    flag=wx.ALL|wx.EXPAND)

        self.ov_progress_label.Hide()
        self.ov_upload_label.Hide()
        self.ov_est_time_label.Hide()
        self.ov_progress_bar.Hide()

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
            value="",
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH)

        value = ("Waiting for user to select directory containing " +
                 "SampleSheet file.\n\n")

        self.status_icon.SetBitmap(self.warning_icon)
        self.log_panel.SetFont(self.TEXTBOX_FONT)
        self.log_panel.SetForegroundColour(self.LOG_PNL_REG_TXT_COLOR)
        self.log_panel.AppendText(value)
        self.log_panel_sizer.Add(self.log_panel, proportion=1, flag=wx.EXPAND)

    def display_warning(self, warn_msg, dlg_msg=""):

        """
        Displays warning message as a popup and writes it in to log_panel

        arguments:
                warn_msg -- message to display in warning dialog message box
                dlg_msg -- optional message to display in warning dialog
                           message box. If this is not an empty string
                           then the string message here will be displayed for
                           the pop up dialog instead of warn_msg.

        no return value
        """

        self.log_color_print(warn_msg + "\n", self.LOG_PNL_ERR_TXT_COLOR)

        if len(dlg_msg) > 0:
            msg = dlg_msg
        else:
            msg = warn_msg

        self.warn_dlg = GMD(
            parent=self, message=msg, caption="Warning!",
            agwStyle=wx.OK | wx.ICON_EXCLAMATION)

        self.warn_dlg.Message = warn_msg  # for testing
        if self.warn_dlg:
            self.warn_dlg.Destroy()

    def log_color_print(self, msg, color=None):

        """
        print colored text to the log_panel
        if no color provided then just uses self.LOG_PNL_REG_TXT_COLOR
        as default

        arguments:
            msg -- the message to print
            color -- the color to print the message in

        no return value
        """

        if color is None:
            color = self.LOG_PNL_REG_TXT_COLOR

        text_attrib = wx.TextAttr(color)

        start_color = len(self.log_panel.GetValue())
        end_color = start_color + len(msg)

        self.log_panel.AppendText(msg)
        self.log_panel.SetStyle(start_color, end_color, text_attrib)
        self.log_panel.AppendText("\n")

    def close_handler(self, event):

        """
        Function bound to window/MainFrame being closed (close button/alt+f4)

        if self.upload_complete is False that means the program was closed
        while an upload was still running.
        Set that SequencingRun's uploadStatus to ERROR.

        Destroy SettingsFrame and then destroy self

        no return value
        """

        self.log_color_print("Closing")
        if all([self.upload_complete is not None,
                self.curr_upload_id is not None,
                self.upload_complete is False]):
            self.log_color_print("Updating sequencing run upload status. " +
                                 "Please wait.", self.LOG_PNL_ERR_TXT_COLOR)
            wx.Yield()
            t = Thread(target=self.api.set_seq_run_error,
                       args=(self.curr_upload_id,))
            t.start()

        self.settings_frame.Destroy()
        self.Destroy()
        sys.exit(0)

    def start_cf_progress_bar_pulse(self):

        """
        pulse self.cf_progress_bar (move bar left and right) until uploading
        sequence file starts
        small indication that program is processing and is not frozen
        the pulse stops when self.pulse_timer.Stop() is called in
        self.update_progress_bars()

        no return value
        """

        pulse_interval = 100  # milliseconds
        self.pulse_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, lambda evt: self.cf_progress_bar.Pulse(),
                  self.pulse_timer)
        self.pulse_timer.Start(pulse_interval)

    def do_online_validation(self):
        wx.CallAfter(self.log_color_print,
                     "Performing online validation on all sequencing runs.\n")

    def handle_online_validation_failure(self, project_id, sample_id):
        wx.CallAfter(self.pulse_timer.Stop)
        wx.CallAfter(self.cf_progress_bar.SetValue, 0)
        wx.CallAfter(self.display_warning, ("Project with ID {project_id} does "
            "not exist (from sample sheet with sample name {sample_id}). Open "
            "SampleSheet.csv and enter the correct project ID for sample "
            "{sample_id}. Once you've corrected the error, you can click 'Upload' "
            "to attempt uploading again.".format(project_id=project_id, sample_id=sample_id)))
        wx.CallAfter(self.start_sample_sheet_processing)

    def start_checking_samples(self):
        wx.CallAfter(self.log_color_print, "Checking samples...")
    def start_uploading_samples(self, sheet_dir, run_id, skipped_sample_ids):
        wx.CallAfter(self.log_color_print, "Starting upload: {}.".format(sheet_dir))
        if run_id and skipped_sample_ids:
            wx.CallAfter(self.log_color_print, "Resuming upload to run with ID: {}\nSkipping already uploaded samples: {}.".format(run_id, ", ".join(skipped_sample_ids)))
    def finished_uploading_samples(self, sheet_dir):
        wx.CallAfter(self.log_color_print, "Finished uploading: {}.".format(sheet_dir))

    def _upload_to_server(self):

        """
        Threaded function from upload_to_server.
        Running on a different thread so that the GUI thread doesn't get
        blocked (i.e the progress bar pulsing doesn't stop/"freeze" when
        making api calls)

        no return value
        """

        if self.api is None:
            raise ConnectionError(
                "Unable to connect to IRIDA. " +
                "View Options -> Settings for more info.")
        for run in self.seq_run_list:
            # used to identify SampleSheet.csv file path
            # when creating a .miseqUploaderInfo in
            # create_miseq_uploader_info_file()
            self.curr_seq_run = run
            upload_run_to_server(self.api, run, self.upload_callback)

    def upload_to_server(self, event):

        """
        Function bound to upload_button being clicked

        pulse the current file progress bar to indicate that processing
        is happening

        make threaded call to self._upload_to_server() which does the
        online validation and upload

        arguments:
                event -- EVT_BUTTON when upload button is clicked

        no return value
        """

        try:
            logging.info("Checking connection before attempting upload")
            self.check_connection(self.api)
        except:
            raise

        pub.subscribe(self.do_online_validation, "start_online_validation")
        pub.subscribe(self.handle_online_validation_failure, "online_validation_failure")
        pub.subscribe(self.start_checking_samples, "start_checking_samples")
        pub.subscribe(self.start_uploading_samples , "start_uploading_samples")
        pub.subscribe(self.finished_uploading_samples, "finished_uploading_samples")

        self.upload_button.Disable()
        # disable upload button to prevent accidental double-click

        self.start_cf_progress_bar_pulse()

        self.log_color_print("Starting upload process")
        t = Thread(target=self._upload_to_server)
        t.daemon = True
        t.start()

    def handle_api_thread_error(self, function_name, exception):

        """
        Subscribed to "handle_api_thread_error"
        Called by any api method when an error occurs
        It's set up this way because api is running
        in a different thread so the regular try-except block wasn't catching
        errors from this function

        arguments:
            function_name -- the name of the function that yielded the error
            exception -- the exception that was raised
        no return value
        """
        wx.CallAfter(self.handle_invalid_sheet_or_seq_file,
            ("The IRIDA server is currently experiencing some difficulty."
            " You can try uploading the run again by clicking 'Upload'."
            " If the error persists, please contact a system administrator."))
        wx.CallAfter(self.start_sample_sheet_processing)

    def seq_files_upload_complete(self):

        """
        Subscribed to message "seq_files_upload_complete".
        This message is going to be sent by ApiCalls.send_sequence_files()
        once all the sequence files have been uploaded.

        Adds to wx events queue: publisher send a message that uploading
        sequence files is complete
        """

        send_message("update_progress_bars", progress_data="Upload Complete")

    def upload_callback(self, monitor):

        """
        callback function used by api.send_sequence_files()
        makes the publisher (pub) send "update_progress_bars" message that
        contains progress percentage data whenever the percentage of the
        current file being uploaded changes.

        arguments:
            monitor -- an encoder.MultipartEncoderMonitor object
                       used for calculating and storing upload percentage data
                       It tracks percentage of overall upload progress
                        and percentage of current file upload progress.
                       the percentages are rounded to `ndigits` decimal place.

        no return value
        """

        ndigits = 4
        monitor.cf_upload_pct = (monitor.bytes_read /
                                 (monitor.len * 1.0))
        monitor.cf_upload_pct = round(monitor.cf_upload_pct, ndigits) * 100

        monitor.total_bytes_read += (monitor.bytes_read - monitor.prev_bytes)
        monitor.ov_upload_pct = (monitor.total_bytes_read /
                                 (monitor.size_of_all_seq_files * 1.0))
        monitor.ov_upload_pct = round(monitor.ov_upload_pct, ndigits) * 100

        for i in xrange(0, len(monitor.files)):
            file = monitor.files[i]
            monitor.files[i] = path.split(file)[1]

        progress_data = {
            "curr_file_upload_pct": monitor.cf_upload_pct,
            "overall_upload_pct": monitor.ov_upload_pct,
            "curr_files_uploading": "\n".join(monitor.files)
        }

        # only call update_progress_bars if one of the % values have changed
        # update estimated remaining time if one of the % values have changed
        if (monitor.prev_cf_pct != monitor.cf_upload_pct or
                monitor.prev_ov_pct != monitor.ov_upload_pct):
            self.update_progress_bars(progress_data)

            elapsed_time = round(time() - monitor.start_time)
            if elapsed_time > 0:

                # bytes
                upload_speed = (monitor.total_bytes_read / elapsed_time)

                ert = ceil(abs((monitor.size_of_all_seq_files -
                               monitor.total_bytes_read) / upload_speed))
                self.update_remaining_time(upload_speed, ert)

        monitor.prev_bytes = monitor.bytes_read
        monitor.prev_cf_pct = monitor.cf_upload_pct
        monitor.prev_ov_pct = monitor.ov_upload_pct

    def get_upload_speed_str(self, upload_speed):

        """
        Constructs upload speed string
        Converts the given upload_speed argument to the largest possible
        metric ((bytes, kilobytes, megabytes, ...) per second) rounded to
        two decimal places

        arguments:
            upload_speed -- float upload speed in bytes per second

        return upload speed string
        """

        metrics = [
            "B/s", "KB/s", "MB/s", "GB/s", "TB/s", "PB/s", "EB/s", "ZB/s"
        ]

        metric_count = 0
        while upload_speed >= 1024.0:
            upload_speed = upload_speed / 1024.0
            metric_count += 1

        upload_speed = round(upload_speed, 2)

        return str(upload_speed) + " " + metrics[metric_count]

    def get_ert_str(self, ert):

        """
        Constructs estimated remaining time string
        Converts the given ert argument to largest possible decimal time
        (seconds, minutes, hours, days)
        Seconds and minutes are rounded to one decimal because the second
        decimal isn't significant compared to hours or days
        Hours or days are rounded to two decimal places

        arguments:
            ert -- float estimated remaining time in seconds
                   must be >= 1

        returns estimated remaining time string
        """

        decimal_time = [
            (1, "seconds"), (60, "minutes"), (60, "hours"), (24, "days")
        ]

        for d in decimal_time:
            if ert >= d[0]:
                ert = ert / d[0]
                rep = d[1]
            else:
                break

        if rep == "minutes" or rep == "seconds":
            ert = int(round(ert))
        else:
            ert = round(ert, 2)

        if ert == 1:  # if value is 1 then remove "s" (e.g minutes to minute)
            rep = rep[:-1]

        return str(ert) + " " + rep

    def update_remaining_time(self, upload_speed, estimated_remaining_time):

        """
        Update the labels for upload speed and estimated remaining time.

        arguments:
            upload_speed -- float upload speed in bytes per second
            estimated_remaining_time -- float est remaining time in seconds
                                        must be >= 1

        no return value
        """

        upload_speed_str = self.get_upload_speed_str(upload_speed)
        estimated_remaining_time_str = self.get_ert_str(
            estimated_remaining_time)

        wx.CallAfter(self.ov_upload_label.SetLabel,
                     self.ov_upload_label_text.format(speed=upload_speed_str))
        wx.CallAfter(self.ov_est_time_label.SetLabel,
                     self.ov_est_time_label_text.format(time=estimated_remaining_time_str))

        wx.CallAfter(self.Layout)

    def update_progress_bars(self, progress_data):

        """
        Subscribed to "update_progress_bars"
        This function is called when pub (publisher) sends the message
        "update_progress_bars"

        Updates boths progress bars and progress labels
        If progress_data is a string equal to "Upload Complete" then
        it calls handle_upload_complete() which displays the
        "Upload Complete" message in the log panel and
        re-enables the upload button.

        arguments:
            progress_data -- dictionary that holds data
                             to be used by the progress bars and labels

        no return value
        """

        if self.pulse_timer.IsRunning():
            self.pulse_timer.Stop()

        if (isinstance(progress_data, str) and
                progress_data == "Upload Complete"):
            self.handle_upload_complete()

        else:
            def _update_progress():
                self.cf_progress_bar.SetValue(
                    progress_data["curr_file_upload_pct"])
                self.cf_progress_label.SetLabel("{files}\n{pct}%".format(
                    files=str(progress_data["curr_files_uploading"]),
                    pct=str(progress_data["curr_file_upload_pct"])))

                if progress_data["overall_upload_pct"] > 100:
                    progress_data["overall_upload_pct"] = 100
                self.ov_progress_bar.SetValue(progress_data
                                              ["overall_upload_pct"])
                self.ov_progress_label.SetLabel("\nOverall: {pct}%".format(
                    pct=str(progress_data["overall_upload_pct"])))
            wx.CallAfter(_update_progress)

    def handle_upload_complete(self):

        """
        function responsible for handling what happens after an upload
        of sequence files finishes
        makes api request to set SequencingRun's uploadStatus in to "Complete"
        displays "Upload Complete" to log panel.
        sets value for Estimated remainnig time to "Complete"
        """

        self.upload_complete = True
        wx.CallAfter(self.log_color_print, "Upload complete\n",
                     self.LOG_PNL_OK_TXT_COLOR)
        wx.CallAfter(self.ov_est_time_label.SetLabel, "Complete")

        wx.CallAfter(self.Layout)

    def display_completion_cmd_msg(self, completion_cmd):
        wx.CallAfter(self.log_color_print,
                     "Executing completion command: " + completion_cmd)

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

        self.status_icon.SetBitmap(self.warning_icon)
        self.display_warning(msg)
        self.upload_button.Disable()

        self.cf_progress_label.Hide()
        self.cf_progress_bar.Hide()
        self.cf_progress_label.SetLabel(self.cf_init_label)
        self.cf_progress_bar.SetValue(0)

        self.ov_progress_label.Hide()
        self.ov_upload_label.Hide()
        self.ov_est_time_label.Hide()
        self.ov_progress_bar.Hide()
        self.ov_progress_label.SetLabel(self.ov_init_label)
        self.ov_upload_label.SetLabel(self.ov_upload_label_text.format(speed="..."))
        self.ov_est_time_label.SetLabel(self.ov_est_time_label_text.format(time="..."))
        self.ov_progress_bar.SetValue(0)

        self.seq_run = None

    def start_sample_sheet_processing(self, evt=None):

        """
        evt is an optional argument that gets passed when this method is invoked
        by an event handler instead of being manually invoked (as at startup)
        """
        self.cf_progress_label.SetLabel(self.cf_init_label)
        self.cf_progress_bar.SetValue(0)
        self.ov_progress_label.SetLabel(self.ov_init_label)

        self.ov_upload_label.SetLabel(self.ov_upload_label_text.format(speed="..."))
        self.ov_est_time_label.SetLabel(self.ov_est_time_label_text.format(time="..."))

        self.ov_progress_bar.SetValue(0)

        # clear the list of sequencing runs and list of samplesheets when user
        # selects a new directory
        self.seq_run_list = []

        browse_path = self.browse_button.GetPath()

        try:
            self.seq_run_list = find_runs_in_directory(browse_path)

            if self.seq_run_list:
                self.status_icon.SetBitmap(self.success_icon)
                self.upload_button.Enable()
                self.cf_progress_label.Show()
                self.cf_progress_bar.Show()
                self.ov_progress_label.Show()
                self.ov_upload_label.Show()
                self.ov_est_time_label.Show()
                self.ov_progress_bar.Show()
                self.log_color_print("List of SampleSheet files to be uploaded:")
                for run in self.seq_run_list:
                    self.log_color_print("{} is valid.".format(run.sample_sheet), self.LOG_PNL_OK_TXT_COLOR)
                self.log_color_print("\n")
                self.Layout()
            elif evt:
                self.handle_invalid_sheet_or_seq_file("No runs in {} are ready for upload. Choose a directory that contains runs that are ready for upload.".format(browse_path))
        except ConnectionError:
            pass
        except Exception as e:
            self.handle_invalid_sheet_or_seq_file(str(e))

    def set_updated_api(self, api):

        """
        Subscribed to message `SettingsFrame.connection_details_changed_topic`.
        This message is sent by SettingsPanel.close_handler().
        When SettingsPanel is closed update self.api to equal the newly created
        ApiCalls object from SettingsPanel

        if the updated self.api is not None re-enable the upload button

        reload self.conf_parser in case it's value (e.g completion_cmd)
        gets updated

        no return value
        """

        self.api = api
        # this updates the UI, possibly from another thread, so we can't
        # call the function directory
        wx.CallAfter(self.check_connection, self.api)
        self.conf_parser.read(self.config_file)

    def check_connection(self, api):
        """Check that the API is connected.

        Arguments:
        api -- the API to check the connection on.
        """


        if self.api and self.api.session:
            self.upload_button.Enable()
        else:
            self.upload_button.Disable()
            if self.api:
                self.log_color_print("Your IRIDA credentials are invalid. Please check the settings dialog to enter new credentials.", self.LOG_PNL_ERR_TXT_COLOR)
            else:
                self.log_color_print("Cannot connect to IRIDA. Please check Options > Settings to enter a new location.", self.LOG_PNL_ERR_TXT_COLOR)
            raise ConnectionError("Unable to connect to IRIDA.")
