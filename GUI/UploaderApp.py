# coding: utf-8
import wx
import threading
import logging
import os

import wx.lib.agw.hyperlink as hl

from wx.lib.wordwrap import wordwrap
from wx.lib.pubsub import pub

from ConfigParser import RawConfigParser
from appdirs import user_config_dir
from requests.exceptions import ConnectionError
from os import path
from urllib2 import URLError

from API.pubsub import send_message
from API.directoryscanner import find_runs_in_directory, DirectoryScannerTopics
from API.runuploader import RunUploader, RunUploaderTopics
from API.apiCalls import ApiCalls

from GUI.SettingsFrame import SettingsFrame
from GUI.Panels import RunPanel, InvalidSampleSheetsPanel

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

        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self._sizer)

        pub.subscribe(self._add_run, DirectoryScannerTopics.run_discovered)
        pub.subscribe(self._finished_loading, DirectoryScannerTopics.finished_run_scan)
        pub.subscribe(self._settings_changed, SettingsFrame.connection_details_changed_topic)
        pub.subscribe(self._sample_sheet_error, DirectoryScannerTopics.garbled_sample_sheet)
        pub.subscribe(self._sample_sheet_error, DirectoryScannerTopics.missing_files)

        self._settings_changed()

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

        # before doing anything, clear all of the children from the sizer and
        # also delete any windows attached (Buttons and stuff extend from Window!)
        self._sizer.Clear(deleteWindows=True)
        # and clear out the list of discovered runs that we might be uploading to the server.
        self._discovered_runs = []
        # initialize the invalid sheets panel so that it can listen for events
        # before directory scanning starts, but hide it until we actually get
        # an error raised by the validation part.
        self._invalid_sheets_panel = InvalidSampleSheetsPanel(self, self._get_default_directory())
        self._invalid_sheets_panel.Hide()
       # run connecting in a different thread so we don't freeze up the GUI
        threading.Thread(target=self._connect_to_irida).start()

    def _get_default_directory(self):
        """Read the default directory from the configuration file.

        Returns:
            A string containing the default directory to scan.
        """
        user_config_file = path.join(user_config_dir("iridaUploader"), "config.conf")

        conf_parser = RawConfigParser()
        conf_parser.read(user_config_file)
        return conf_parser.get("Settings", "default_dir")

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
        user_config_file = path.join(user_config_dir("iridaUploader"), "config.conf")

        conf_parser = RawConfigParser()
        conf_parser.read(user_config_file)

        client_id = conf_parser.get("Settings", "client_id")
        client_secret = conf_parser.get("Settings", "client_secret")
        baseURL = conf_parser.get("Settings", "baseURL")
        username = conf_parser.get("Settings", "username")
        password = conf_parser.get("Settings", "password")

        try:
            api = ApiCalls(client_id, client_secret, baseURL, username, password)
            self._api = api

            # only bother scanning once we've connected to IRIDA
            wx.CallAfter(self._scan_directories)
        except ConnectionError, e:
            logging.info("Got a connection error when trying to connect to IRIDA.", exc_info=True)
            wx.CallAfter(self._handle_connection_error, error_message=(
                "We couldn't connect to IRIDA at {}. The server might be down. Make "
                "sure that the connection address is correct (you can change the "
                "address by clicking on the 'Open Settings' button below) and try"
                " again, try again later, or contact an administrator."
                ).format(baseURL))
        except (SyntaxError, ValueError) as e:
            logging.info("Connected, but the response was garbled.", exc_info=True)
            wx.CallAfter(self._handle_connection_error, error_message=(
                "We couldn't connect to IRIDA at {}. The server is up, but I "
                "didn't understand the response. Make sure that the connection "
                "address is correct (you can change the address by clicking on "
                "the 'Open Settings' button below) and try again, try again"
                " later, or contact an administrator."
                ).format(baseURL))
        except KeyError, e:
            logging.info("Connected, but the OAuth credentials are wrong.", exc_info=True)
            wx.CallAfter(self._handle_connection_error, error_message=(
                "We couldn't connect to IRIDA at {}. The server is up, but it's "
                "reporting that your credentials are wrong. Click on the 'Open Settings'"
                " button below and check your credentials, then try again. If the "
                "connection still doesn't work, contact an administrator."
                ).format(baseURL))
        except URLError, e:
            logging.info("Couldn't connect to IRIDA because the URL is invalid.", exc_info=True)
            wx.CallAfter(self._handle_connection_error, error_message=(
                "We couldn't connect to IRIDA at {} because it isn't a valid URL. "
                "Click on the 'Open Settings' button below to enter a new URL and "
                "try again."
            ).format(baseURL))
    	except:
    	    logging.info("Some other kind of error happened.", exc_info=True)
            wx.CallAfter(self._handle_connection_error, error_message=(
                "We couldn't connect to IRIDA at {} for an unknown reason. Click "
                "on the 'Open Settings' button below to check the URL and your "
                "credentials, then try again. If the connection still doesn't "
                "work, contact an administrator."
                ).format(baseURL))

    def _handle_connection_error(self, error_message=None):
    	"""Handle connection errors that might be thrown when initially connecting to IRIDA.

    	Args:
    	    error_message: A more detailed error message than "Can't connect"
    	"""

        logging.error("Handling connection error.")

        self.Freeze()

        connection_error_sizer = wx.BoxSizer(wx.HORIZONTAL)
        connection_error_header = wx.StaticText(self, label="✘ Uh-oh. I couldn't to connect to IRIDA.")
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

    def _finished_loading(self):
        """Update the display when the run scan is finished.

        When the `DirectoryScannerTopics.finished_run_scan` topic is received, add
        the upload button to the page so that the user can start the upload.
        """
        if not self._invalid_sheets_panel.IsShown():
            self.Freeze()
            if self._discovered_runs:
                upload_button = wx.Button(self, label="Upload")
                self._upload_sizer.Add(upload_button, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=5)
                self.Bind(wx.EVT_BUTTON, self._start_upload, id=upload_button.GetId())
            else:
                all_uploaded_sizer = wx.BoxSizer(wx.HORIZONTAL)
                all_uploaded_header = wx.StaticText(self, label="✓ All sample sheets uploaded.")
                all_uploaded_header.SetFont(wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.BOLD))
                all_uploaded_header.SetForegroundColour(wx.Colour(0, 255, 0))
                all_uploaded_header.Wrap(350)
                all_uploaded_sizer.Add(all_uploaded_header, flag=wx.LEFT | wx.RIGHT, border=5)

                self._sizer.Add(all_uploaded_sizer, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=5)
                self._sizer.Add(wx.StaticText(self, label=wordwrap("I scanned {}, but I didn't find any sample sheets that weren't already uploaded.".format(self._get_default_directory()), 350, wx.ClientDC(self))), flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=5)

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

        run_panel = RunPanel(self, run, self._api)
        self.Freeze()
        self._run_sizer.Add(run_panel, flag=wx.EXPAND, proportion=1)
        self.Layout()
        self.Thaw()

    def _start_upload(self, event):
        """Initiate uploading runs to the server.

        This will upload multiple runs simultaneously, one per thread.

        Args:
            event: the button event that initiated the method.
        """

        self._upload_thread = RunUploader(api=self._api, runs=self._discovered_runs)
        self._upload_thread.start()

    def Destroy(self):
        self._upload_thread.join()
        wx.Panel.Destroy(self)

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
