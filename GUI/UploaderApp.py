import wx
import threading
import logging

from wx.lib.wordwrap import wordwrap
from wx.lib.pubsub import pub

from ConfigParser import RawConfigParser
from appdirs import user_config_dir

from os import path

from API.pubsub import send_message
from API.directoryscanner import find_runs_in_directory, DirectoryScannerTopics
from API.runuploader import upload_run_to_server, RunUploaderTopics

from GUI.SettingsFrame import SettingsFrame
from GUI.Panels import RunPanel

class UploaderAppPanel(wx.ScrolledWindow):
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
    """
    def __init__(self, parent):
        """Initialize the UploaderAppPanel.

        Args:
            parent: the parent Window for this panel.
        """
        wx.ScrolledWindow.__init__(self, parent, style=wx.VSCROLL)
        self.SetScrollRate(xstep=20, ystep=20)

        self._discovered_runs = []

        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self._sizer)
        self._run_sizer = wx.BoxSizer(wx.VERTICAL)
        self._upload_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self._sizer.Add(self._run_sizer, proportion=1, flag=wx.TOP | wx.EXPAND)
        self._sizer.Add(self._upload_sizer, proportion=0, flag=wx.BOTTOM | wx.ALIGN_CENTER)

        # start scanning the runs directory immediately
        pub.subscribe(self._add_run, DirectoryScannerTopics.run_discovered)
        pub.subscribe(self._finished_loading, DirectoryScannerTopics.finished_run_scan)
        logging.info("Starting to scan [{}] for sequencing runs.".format(self._get_default_directory()))
        threading.Thread(target=find_runs_in_directory, kwargs={"directory": self._get_default_directory()}).start()

    def _get_default_directory(self):
        """Read the default directory from the configuration file.

        Returns:
            A string containing the default directory to scan.
        """
        user_config_file = path.join(user_config_dir("iridaUploader"), "config.conf")

        conf_parser = RawConfigParser()
        conf_parser.read(user_config_file)
        return conf_parser.get("Settings", "default_dir")

    def _finished_loading(self):
        """Update the display when the run scan is finished.

        When the `DirectoryScannerTopics.finished_run_scan` topic is received, add
        the upload button to the page so that the user can start the upload.
        """
        self.Freeze()
        upload_button = wx.Button(self, label="Upload")
        self._upload_sizer.Add(upload_button, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=5)
        self.Bind(wx.EVT_BUTTON, self._start_upload, id=upload_button.GetId())
        self.Layout()
        self.Thaw()

    def _add_run(self, run):
        """Update the display to add a new `RunPanel`.

        When the `DirectoryScannerTopics.run_discovered` topic is received, add
        the run to the display.

        Args:
            run: the run to add to the display.
        """
        logging.info("Adding run [{}]".format(run.sample_sheet_dir))
        self._discovered_runs.append(run)

        ## this is **extraordinarily** yucky, but I just want access to the API
        settings = SettingsFrame(self)
        api = settings.attempt_connect_to_api()

        run_panel = RunPanel(self, run, api)
        self.Freeze()
        self._run_sizer.Add(run_panel, flag=wx.EXPAND)
        self.Layout()
        self.Thaw()

    def _start_upload(self, event):
        """Initiate uploading runs to the server.

        This will upload multiple runs simultaneously, one per thread.

        Args:
            event: the button event that initiated the method.
        """
        for run in self._discovered_runs:
            logging.info("Starting upload for {}".format(run.sample_sheet_dir))
            ## this is **extraordinarily** yucky, but I just want access to the API
            settings = SettingsFrame(self)
            api = settings.attempt_connect_to_api()

            threading.Thread(target=upload_run_to_server, kwargs={"api": api, "sequencing_run": run, "progress_callback": None}).start()

class UploaderAppFrame(wx.Frame):
    """The UploaderAppFrame is the super-container the Application.

        The frame sets up the menu and adds an "About" dialog.
    """

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
                          800, 1200) # max window size
        self.Show(True)

    def _build_menu(self):
        """Build the application menu."""
        menubar = wx.MenuBar()
        file_menu = wx.Menu()
        help_menu = wx.Menu()

        self.Bind(wx.EVT_MENU, self._open_settings, file_menu.Append(wx.ID_PROPERTIES, 'Settings...'))
        file_menu.AppendSeparator()
        self.Bind(wx.EVT_MENU, lambda evt: self.Close(), file_menu.Append(wx.ID_EXIT))
        self.Bind(wx.EVT_MENU, self._open_about, help_menu.Append(wx.ID_ABOUT))

        menubar.Append(file_menu, '&File')
        menubar.Append(help_menu, '&Help')
        self.SetMenuBar(menubar)

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
        settings = SettingsFrame(self)
        # attempt to connect to the API *before* showing so that the icons are
        # all initialized correctly.
        settings.attempt_connect_to_api()
        settings.Show()
