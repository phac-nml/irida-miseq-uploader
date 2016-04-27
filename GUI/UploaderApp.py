import wx
import threading
import logging

from wx.lib.wordwrap import wordwrap
from wx.lib.pubsub import pub

from API.pubsub import send_message

from GUI import SettingsFrame
from GUI.Panels import RunPanel
from API.directoryscanner import find_runs_in_directory
from API.runuploader import upload_run_to_server

class UploaderAppPanel(wx.ScrolledWindow):
    def __init__(self, parent):
        wx.ScrolledWindow.__init__(self, parent, style=wx.VSCROLL)
        self.SetScrollRate(xstep=20, ystep=20)

        self._discovered_runs = []

        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self._sizer)
        self._run_sizer = wx.BoxSizer(wx.VERTICAL)
        self._upload_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self._sizer.Add(self._run_sizer, proportion=1, flag=wx.TOP | wx.EXPAND)
        self._sizer.Add(self._upload_sizer, proportion=0, flag=wx.BOTTOM | wx.ALIGN_CENTER)

        upload_button = wx.Button(self, label="Upload")
        self._upload_sizer.Add(upload_button, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=5)
        self.Bind(wx.EVT_BUTTON, self._start_upload, id=upload_button.GetId())

        # start scanning the runs directory immediately
        pub.subscribe(self._add_run, "run_discovered")
        threading.Thread(target=find_runs_in_directory, kwargs={"directory":"/home/fbristow/Downloads/irida-sample-data"}).start()

    def _add_run(self, run):
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
        for run in self._discovered_runs:
            logging.info("Starting upload for {}".format(run.sample_sheet_dir))
            ## this is **extraordinarily** yucky, but I just want access to the API
            settings = SettingsFrame(self)
            api = settings.attempt_connect_to_api()

            threading.Thread(target=upload_run_to_server, kwargs={"api": api, "sequencing_run": run, "progress_callback": None}).start()

class UploaderAppFrame(wx.Frame):
    def __init__(self, parent=None, app_name=None, app_version=None, app_url=None, *args, **kwargs):
        wx.Frame.__init__(self, parent, *args, **kwargs)
        self._app_name = app_name
        self._app_version = app_version
        self._app_url = app_url

        self._build_menu()
        UploaderAppPanel(self)

        self.SetTitle(self._app_name)
        self.Show(True)

    def _build_menu(self):
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
        app_info = wx.AboutDialogInfo()
        app_info.Name = self._app_name
        app_info.Version = self._app_version
        app_info.WebSite = (self._app_url, "IRIDA Uploader on GitHub")
        app_info.Description = wordwrap("IRIDA Uploader is a tool to send Illumina MiSeq data to an instance of IRIDA for management.", 350, wx.ClientDC(self))

        wx.AboutBox(app_info)

    def _open_settings(self, event):
        settings = SettingsFrame(self)
        settings.Show()
