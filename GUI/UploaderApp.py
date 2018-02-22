# coding: utf-8
import wx
import threading
import logging
import os

import wx.lib.agw.hyperlink as hl

from wx.lib.wordwrap import wordwrap
from wx.lib.pubsub import pub

from API.pubsub import send_message
from API.directoryscanner import find_runs_in_directory, DirectoryScannerTopics
from API.directorymonitor import RunMonitor, DirectoryMonitorTopics
from API.runuploader import RunUploader, RunUploaderTopics
from API.apiCalls import ApiCalls
from API.APIConnector import connect_to_irida, APIConnectorTopics
from API.config import read_config_option

from GUI.Panels import RunPanel, InvalidSampleSheetsPanel
from GUI.SettingsDialog import SettingsDialog
from GUI.ProcessingPlaceholderText import ProcessingPlaceholderText

condition = threading.Condition()

class UploaderAppPanel(wx.Panel):
    """The UploaderAppPanel is the super-container the discovered SequencingRuns.

    This panel is used to display the runs that are discovered. It's a scrolling
    window so that if the run has too many samples, the user will be able to scroll
    around so we don't have a super-huge display.

    Subscriptions:
        DirectoryScannerTopics.run_discovered: A run has been discovered during
            directory scanning. Accepts one argument: the run that was discovered.
            This will initiate adding the run to the panel.
        DirectoryScannerTopics.finished_run_scan: Run scanning has completed, so
            (if everything is in a valid state) add the upload button to the panel.
        SettingsFrame.connection_details_changed_topic: The connection details
            have changed (typically when there's invalid URL settings) so the
            connection attempt should be retried.
        DirectoryScannerTopics.garbled_sample_sheet: The sample sheet could not
            be processed by the sample sheet processor, so errors should be displayed
            to the client.
    """
    def __init__(self, parent):
        """Initialize the UploaderAppPanel.

        Args:
            parent: the parent Window for this panel.
        """
        wx.Panel.__init__(self, parent)
        self._parent = parent
        self._discovered_runs = []
        self._selected_directory = None
        self._monitor_thread = None

        self._sizer = wx.BoxSizer(wx.VERTICAL)

        # topics to handle from directory scanning
        pub.subscribe(self._add_run, DirectoryScannerTopics.run_discovered)
        pub.subscribe(self._finished_loading, DirectoryScannerTopics.finished_run_scan)
        pub.subscribe(self._sample_sheet_error, DirectoryScannerTopics.garbled_sample_sheet)
        pub.subscribe(self._sample_sheet_error, DirectoryScannerTopics.missing_files)
        # topics to handle when settings have changed in the settings frame
        pub.subscribe(self._settings_changed, SettingsDialog.settings_closed_topic)
        pub.subscribe(self._shutdown_monitoring, DirectoryMonitorTopics.shut_down_directory_monitor)
        pub.subscribe(self._restart_monitorting, DirectoryMonitorTopics.start_up_directory_monitor)
        # topics to handle when a directory is selected by File > Open
        pub.subscribe(self._directory_selected, UploaderAppFrame.directory_selected_topic)

        self._settings_changed()
        self.SetSizerAndFit(self._sizer)

    def _prepare_for_automatic_upload(self):
        """Clear out anything else that happens to be on the panel before Starting
        an automatic upload."""

        self.Freeze()
        self._sizer.Clear(deleteWindows=True)
        self._discovered_runs = []

        self._run_sizer = wx.BoxSizer(wx.VERTICAL)
        self._upload_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self._sizer.Add(self._run_sizer, proportion=1, flag=wx.EXPAND)
        self._sizer.Add(self._upload_sizer, proportion=0, flag=wx.ALIGN_CENTER)
        self.Layout()
        self.Thaw()

    def _directory_selected(self, directory):
        """The user has selected a different directory from default, so restart
        scanning using the selected directory.

        Args:
            directory: The directory to scan.
        """
        self._selected_directory = directory
        wx.CallAfter(self._settings_changed)

    def _sample_sheet_error(self, sample_sheet=None, error=None):
        """Show the invalid sample sheets panel whenever a sample sheet error
        is raised.

        Args:
            sample_sheet: the sample sheet that's got the error
            error: the validation error
        """
        if not self._invalid_sheets_panel.IsShown():
            self.Freeze()
            # clear out the other panels that might already be added
            self._sizer.Clear(deleteWindows=True)
            # add the sheets panel to the sizer and show it
            self._sizer.Add(self._invalid_sheets_panel, flag=wx.EXPAND, proportion=1)
            self._invalid_sheets_panel.Show()
            self.Layout()
            self.Thaw()

    def _settings_changed(self, api=None):
    	"""Reset the main display and attempt to connect to the server
    	   whenever the connection settings may have changed.

     	Args:
    	    api: A placeholder for a complete api that's passed when the event is fired.
    	"""

        global condition
        # before doing anything, clear all of the children from the sizer and
        # also delete any windows attached (Buttons and stuff extend from Window!)
        self.Freeze()
        self._sizer.Clear(deleteWindows=True)
        # and clear out the list of discovered runs that we might be uploading to the server.
        self._discovered_runs = []
        # initialize the invalid sheets panel so that it can listen for events
        # before directory scanning starts, but hide it until we actually get
        # an error raised by the validation part.
        self._invalid_sheets_panel = InvalidSampleSheetsPanel(self, self._get_default_directory())
        self._invalid_sheets_panel.Hide()
        self._should_monitor_directory = read_config_option("monitor_default_dir", expected_type=bool, default_value=False)
        self.Layout()
        self.Thaw()
        if self._should_monitor_directory:
            self.Freeze()
            self._display_auto()
            self._display_samplesheet_upload()
            self.Layout()
            self.Thaw()
            if self._monitor_thread is None:
                send_message(DirectoryMonitorTopics.start_up_directory_monitor)
            else:
                logging.info("Continuing to monitor default directory [{}] for new runs.".format(self._get_default_directory()))
        else:
            logging.info("shutting down any existing version of directory monitor")
            send_message(DirectoryMonitorTopics.shut_down_directory_monitor)

        # run connecting in a different thread so we don't freeze up the GUI
        threading.Thread(target=self._connect_to_irida).start()

    def _shutdown_monitoring(self):
        """tasks to be compled when monitoring is turned off"""
        try: 
            if pub.isSubscribed(self._prepare_for_automatic_upload, DirectoryMonitorTopics.new_run_observed):
                logging.info("Unsubscribing auto subscriptions")
                pub.unsubscribe(self._prepare_for_automatic_upload, DirectoryMonitorTopics.new_run_observed)
                pub.unsubscribe(self._start_upload, DirectoryMonitorTopics.finished_discovering_run)
                self._monitor_thread = None
        except ValueError:
            logging.info("_prepare_for_automatic_upload not yet subscribed to anything")
        
    def _restart_monitorting(self):
        """tasks to be compled when monitoring is turned on"""
        if self._monitor_thread is None:
            logging.info("Going to start monitoring default directory [{}] for new runs.".format(self._get_default_directory()))
            pub.subscribe(self._prepare_for_automatic_upload, DirectoryMonitorTopics.new_run_observed)
            pub.subscribe(self._start_upload, DirectoryMonitorTopics.finished_discovering_run)
            self._monitor_thread = RunMonitor(directory=self._get_default_directory(), cond=condition)
            self._monitor_thread.start()

    def _scan_button(self, api=None):
        """Turns off auto upload monitor when the "Scan" button is pressed. Must turn off
        auto upload to prevent collision of the scan and the auto both finding
        the same data at the same time and to prevent auto from kicking in during the scan.
        Once this is turned off, _scan_directories is called. In _finished_upload, auto is resumed
        """
        self.Freeze()
        self._sizer.Clear(deleteWindows=True)
        self.Layout()
        self.Thaw()
        if self._should_monitor_directory:
            logging.info("shutting down any existing version of directory monitor")
            send_message(DirectoryMonitorTopics.shut_down_directory_monitor)
        self._scan_directories()
     
    def _get_default_directory(self):
        """Read the default directory from the configuration file, or, if the user
        has selected a directory manually, return the manually selected directory.

        Returns:
            A string containing the default directory to scan.
        """

        if not self._selected_directory:
            return read_config_option("default_dir")
        else:
            return self._selected_directory

    def _scan_directories(self):
        """Begin scanning directories for the default directory."""
        
        logging.info("Starting to scan [{}] for sequencing runs.".format(self._get_default_directory()))
        self.Freeze()
        self._run_sizer = wx.BoxSizer(wx.VERTICAL)
        self._upload_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self._sizer.Add(self._run_sizer, proportion=1, flag=wx.EXPAND)
        self._sizer.Add(self._upload_sizer, proportion=0, flag=wx.ALIGN_CENTER)
        self.Layout()
        self.Thaw()
        threading.Thread(target=find_runs_in_directory, kwargs={"directory": self._get_default_directory()}).start()

    def _connect_to_irida(self):
        """Connect to IRIDA for online validation.

        Returns:
            A configured instance of API.apiCalls.
        """
        pub.subscribe(self._handle_connection_error, APIConnectorTopics.connection_error_topic)
        try:
            self._api = connect_to_irida()
        except:
            logging.info("Failed to connect to IRIDA, handling error.")
            # error handling is done by subscriptions.
        else:
            if not self._should_monitor_directory:
                # only bother scanning once we've connected to IRIDA and only scan directories if monitoring not on
                wx.CallAfter(self._scan_directories)

    def _handle_connection_error(self, error_message=None):
        """Handle connection errors that might be thrown when initially connecting to IRIDA.

        Args:
            error_message: A more detailed error message than "Can't connect"
        """

        logging.error("Handling connection error.")
        # stop monitoring directory until connection error is solved
        if self._should_monitor_directory:
            logging.info("shutting down any existing version of directory monitor")
            send_message(DirectoryMonitorTopics.shut_down_directory_monitor)
            self._monitor_thread = None
        self.Freeze()
        # clear out the other panels that might already be added
        self._sizer.Clear(deleteWindows=True)
        connection_error_sizer = wx.BoxSizer(wx.HORIZONTAL)
        connection_error_header = wx.StaticText(self, label=u"✘ Uh-oh. I couldn't to connect to IRIDA.")
        connection_error_header.SetFont(wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        connection_error_header.SetForegroundColour(wx.Colour(255, 0, 0))
        connection_error_header.Wrap(350)
        connection_error_sizer.Add(connection_error_header, flag=wx.LEFT | wx.RIGHT, border=5)

        self._sizer.Add(connection_error_sizer, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=5)
        if error_message:
            self._sizer.Add(wx.StaticText(self, label=wordwrap(error_message, 350, wx.ClientDC(self))), flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=5)

        open_settings_button = wx.Button(self, label="Open Settings")
        self.Bind(wx.EVT_BUTTON, self._parent._open_settings, id=open_settings_button.GetId())
        self._sizer.Add(open_settings_button, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=5)

        self.Layout()
        self.Thaw()
        pub.unsubscribe(self._handle_connection_error, APIConnectorTopics.connection_error_topic)

    def _finished_loading(self):
        """Update the display when the run scan is finished.

        When the `DirectoryScannerTopics.finished_run_scan` topic is received, add
        the upload button to the page so that the user can start the upload.
        """
        if not self._invalid_sheets_panel.IsShown():
            if self._discovered_runs:
                self.Freeze()
                upload_button = wx.Button(self, label="Upload")
                self._upload_sizer.Add(upload_button, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=5)
                self.Bind(wx.EVT_BUTTON, self._start_upload, id=upload_button.GetId())
                self.Layout()
                self.Thaw()
            else:
                self._finished_upload()

    def _finished_upload(self):
        """Update the display and resume auto upload if necessary 
        when the upload is finished.
        """
        if self._should_monitor_directory:
            self._settings_changed()
        else:
            self.Freeze()
            self._sizer.Clear(deleteWindows=True)
            self._display_samplesheet_upload()
            self.Layout()
            self.Thaw()
        pub.subscribe(self._finished_loading, DirectoryScannerTopics.finished_run_scan)
        pub.unsubscribe(self._start_upload, DirectoryScannerTopics.finished_run_scan)


    def _display_samplesheet_upload(self):
        """Displays a message that a sample sheet has been uploaded 
        and nothing else needs to be uploaded
        """
        all_uploaded_sizer = wx.BoxSizer(wx.HORIZONTAL)
        all_uploaded_header = wx.StaticText(self, label=u"✓ Sample sheet was uploaded.")
        all_uploaded_header.SetFont(wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        all_uploaded_header.SetForegroundColour(wx.Colour(51, 204, 51))
        all_uploaded_header.Wrap(350)
        all_uploaded_sizer.Add(all_uploaded_header, flag=wx.LEFT | wx.RIGHT, border=5)

        self._sizer.Add(all_uploaded_sizer, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=5)

        all_uploaded_details = wx.StaticText(self, label="Finished uploading. Click 'Scan' to try finding new runs.".format(self._get_default_directory()))
        all_uploaded_details.Wrap(350)

        self._sizer.Add(all_uploaded_details, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=5)

        scan_again = wx.Button(self, label="Scan")
        self._sizer.Add(scan_again, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=5)
        self.Bind(wx.EVT_BUTTON, self._scan_button, id=scan_again.GetId())

    def _display_auto(self):
        """Displays that automatic upload enabled message.
        """
        automatic_upload_status_sizer = wx.BoxSizer(wx.HORIZONTAL)
        auto_upload_enabled_text = wx.StaticText(self, label=u"⇌ Automatic upload enabled.")
        auto_upload_enabled_text.SetFont(wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        auto_upload_enabled_text.SetForegroundColour(wx.Colour(51, 102, 255))
        auto_upload_enabled_text.SetToolTipString("Monitoring {} for CompletedJobInfo.xml".format(self._get_default_directory()))
        automatic_upload_status_sizer.Add(auto_upload_enabled_text, flag=wx.LEFT | wx.RIGHT, border=5)
        self._sizer.Add(automatic_upload_status_sizer, flag=wx.ALIGN_CENTER | wx.ALL, border=5)

    def _add_run(self, run):
        """Update the display to add a new `RunPanel`.

        When the `DirectoryScannerTopics.run_discovered` topic is received, add
        the run to the display.

        Args:
            run: the run to add to the display.
        """
        logging.info("Adding run [{}]".format(run.sample_sheet_dir))
        self._discovered_runs.append(run)

        run_panel = RunPanel(self, run, self._api)
        pub.subscribe(self._upload_failed, run.upload_failed_topic)

        self.Freeze()
        self._run_sizer.Add(run_panel, flag=wx.EXPAND, proportion=1)
        self.Layout()
        self.Thaw()

    def _upload_failed(self, exception=None):
        """The upload failed, add a button to restart the upload.

        Args:
            exception: the error that caused the upload.
        """
        logging.info("Adding try again button on upload failure.")
        self.Freeze()
        try_again = wx.Button(self, label="Try again")
        self._upload_sizer.Add(try_again, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=5)
        self.Bind(wx.EVT_BUTTON, self._retry_upload, id=try_again.GetId())
        self.Layout()
        self.Thaw()
        if self._should_monitor_directory:
            # turn off monitoring to prevent the monitoring while an error is being dealt with
            # by the user. If monitoring was to continue, the GUI would refresh. As there is a 
            # .miseqinfo file created, the erroring run would not appear again and thus the 
            # error wouldn't be displayed to the user again. 
            logging.info("shutting down any existing version of directory monitor")
            send_message(DirectoryMonitorTopics.shut_down_directory_monitor)
 
    def _retry_upload(self, evt=None):
        """Retry the upload after a failure is encountered.

        Args:
            evt: the event that fired this upload.
        """
        self._prepare_for_automatic_upload()
        pub.unsubscribe(self._finished_loading, DirectoryScannerTopics.finished_run_scan)
        pub.subscribe(self._start_upload, DirectoryScannerTopics.finished_run_scan)
        find_runs_in_directory(self._get_default_directory())

    def _start_upload(self, *args, **kwargs):
        """Initiate uploading runs to the server.

        This will upload multiple runs simultaneously, one per thread.

        Args:
            event: the button event that initiated the method.
        """
        global condition
        if self._discovered_runs:
            post_processing_task = read_config_option("completion_cmd")
            logging.debug("Running upload for {}".format(str(self._discovered_runs)))
            
            pub.subscribe(self._post_processing_task_started, RunUploaderTopics.started_post_processing)
            
            pub.subscribe(self._finished_upload, RunUploaderTopics.finished_uploading_samples)
            # pass the lock to the RunUploader
            self._upload_thread = RunUploader(api=self._api, runs=self._discovered_runs, cond=condition, post_processing_task=post_processing_task)
            # destroy the upload button once it's been clicked.
            self.Freeze()
            self._upload_sizer.Clear(True)
            self.Layout()
            self.Thaw()
            self._upload_thread.start()
        else:
            logging.info("nothing to upload")
            # release the lock as there was nothing to upload
            condition.acquire()
            condition.notify()
            condition.release()

    def _post_processing_task_started(self):
        """Show a 'processing' message on the UI while the post processing task is executing."""
        pub.unsubscribe(self._post_processing_task_started, RunUploaderTopics.started_post_processing)
        pub.subscribe(self._post_processing_task_completed, RunUploaderTopics.finished_post_processing)
        pub.subscribe(self._post_processing_task_failed, RunUploaderTopics.failed_post_processing)
        logging.info("Post-processing started, updating UI.")

        self.Freeze()
        self._post_processing_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._post_processing_placeholder = ProcessingPlaceholderText(self)
        self._post_processing_placeholder.SetFont(wx.Font(pointSize=18, family=wx.FONTFAMILY_DEFAULT, style=wx.NORMAL, weight=wx.FONTWEIGHT_BOLD, face="Segoe UI Symbol"))
        self._post_processing_text = wx.StaticText(self, label="Executing post-processing task.")
        self._post_processing_text.SetFont(wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        self._post_processing_text.Wrap(350)
        self._post_processing_text.SetToolTipString("Executing command `{}`.".format(read_config_option("completion_cmd")))
        self._post_processing_sizer.Add(self._post_processing_text, flag=wx.RIGHT, border=5, proportion=1)
        self._post_processing_sizer.Add(self._post_processing_placeholder, flag=wx.LEFT, border=5, proportion=0)

        self._sizer.Insert(0, self._post_processing_sizer, flag=wx.EXPAND | wx.ALL, border=5)
        self.Layout()
        self.Thaw()

    def _post_processing_task_completed(self):
        """Show a 'completed' message on the UI when the post processing task is finished."""
        pub.unsubscribe(self._post_processing_task_completed, RunUploaderTopics.finished_post_processing)
        pub.unsubscribe(self._post_processing_task_failed, RunUploaderTopics.failed_post_processing)
        logging.info("Post-processing finished, updating UI.")
        self.Freeze()
        self._post_processing_text.SetLabel("Post-processing task complete.")
        self._post_processing_text.SetToolTipString("Successfully executed command `{}`.".format(read_config_option("completion_cmd")))
        self._post_processing_text.Wrap(350)
        self._post_processing_placeholder.SetSuccess()
        self.Layout()
        self.Thaw()

    def _post_processing_task_failed(self):
        """Show a 'failed' message on the UI when the post processing task fails."""
        pub.unsubscribe(self._post_processing_task_failed, RunUploaderTopics.failed_post_processing)
        pub.unsubscribe(self._post_processing_task_completed, RunUploaderTopics.finished_post_processing)
        logging.info("Post-processing failed, updating UI.")
        self.Freeze()
        self._post_processing_text.SetLabel("Post-processing task failed.")
        self._post_processing_text.SetToolTipString("Failed to execute command `{}`.".format(read_config_option("completion_cmd")))
        self._post_processing_text.Wrap(350)
        self._post_processing_placeholder.SetError("Failed to execute command `{}`.".format(read_config_option("completion_cmd")))
        self.Layout()
        self.Thaw()

    def Destroy(self):
        self._upload_thread.join()
        if self._monitor_thread is not None:
            self._monitor_thread.join()
            send_message(DirectoryMonitorTopics.shut_down_directory_monitor)
        wx.Panel.Destroy(self)

class UploaderAppFrame(wx.Frame):
    """The UploaderAppFrame is the super-container the Application.

        The frame sets up the menu and adds an "About" dialog.
    """

    directory_selected_topic = "directory_selected_topic"

    def __init__(self, parent=None, app_name=None, app_version=None, app_url=None, *args, **kwargs):
        """Initialize the UploaderAppFrame

        Args:
            parent: the parent of this Frame
            app_name: the name of the application (used as the window title and
                in the about dialog)
            app_version: the version of the application (used in the about dialog)
            app_url: the url of the application (used in the about dialog)
        """
        wx.Frame.__init__(self, parent, *args, **kwargs)
        self._app_name = app_name
        self._app_version = app_version
        self._app_url = app_url

        self._build_menu()
        UploaderAppPanel(self)

        self.SetTitle(self._app_name)
        self.SetSizeHints(400, 600,  # min window size
                          800, 700) # max window size (miseq has 1024x768 display resolution)
        self.Show(True)

    def _build_menu(self):
        """Build the application menu."""
        menubar = wx.MenuBar()
        file_menu = wx.Menu()
        help_menu = wx.Menu()

        self.Bind(wx.EVT_MENU, self._directory_chooser, file_menu.Append(wx.ID_OPEN, 'Open directory...'))
        self.Bind(wx.EVT_MENU, self._open_settings, file_menu.Append(wx.ID_PROPERTIES, 'Settings...'))
        file_menu.AppendSeparator()
        self.Bind(wx.EVT_MENU, lambda evt: self.Close(), file_menu.Append(wx.ID_EXIT))
        self.Bind(wx.EVT_MENU, self._open_about, help_menu.Append(wx.ID_ABOUT))
        self.Bind(wx.EVT_MENU, lambda evt: wx.LaunchDefaultBrowser("http://irida-miseq-uploader.readthedocs.io/en/latest/"), help_menu.Append(wx.ID_HELP))

        menubar.Append(file_menu, '&File')
        menubar.Append(help_menu, '&Help')
        self.SetMenuBar(menubar)

    def _directory_chooser(self, event):
        """Open a directory chooser to select a directory other than default."""
        logging.info("Going to open a folder chooser")
        dir_dialog = wx.DirDialog(self, style=wx.DD_DIR_MUST_EXIST)
        response = dir_dialog.ShowModal()

        if response == wx.ID_OK:
            logging.info("User selected directory [{}]".format(dir_dialog.GetPath()))
            send_message(UploaderAppFrame.directory_selected_topic, directory=dir_dialog.GetPath())

    def _open_about(self, event):
        """Open the about dialog."""
        app_info = wx.AboutDialogInfo()
        app_info.Name = self._app_name
        app_info.Version = self._app_version
        app_info.WebSite = (self._app_url, "IRIDA Uploader on GitHub")
        app_info.Description = wordwrap("IRIDA Uploader is a tool to send Illumina MiSeq data to an instance of IRIDA for management.", 350, wx.ClientDC(self))

        wx.AboutBox(app_info)

    def _open_settings(self, event):
        """Open the settings dialog."""
        dialog = SettingsDialog(self)
        dialog.ShowModal()
