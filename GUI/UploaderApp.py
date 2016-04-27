import wx
import threading
import logging

from wx.lib.wordwrap import wordwrap
from wx.lib.pubsub import pub

from GUI import SettingsFrame
from GUI.Panels import RunPanel
from API.directoryscanner import find_runs_in_directory

class UploaderAppFrame(wx.Frame):
    def __init__(self, parent=None, app_name=None, app_version=None, app_url=None, *args, **kwargs):
        wx.Frame.__init__(self, parent, *args, **kwargs)
        self._app_name = app_name
        self._app_version = app_version
        self._app_url = app_url

        self._build_menu()
        self._add_panel()

        self.SetTitle(self._app_name)
        self.Show(True)

    def _add_panel(self):
        self._run_panel = wx.Panel(self, wx.ID_ANY)
        self._run_sizer = wx.BoxSizer(wx.VERTICAL)
        self._run_panel.SetSizer(self._run_sizer)

        # start scanning the runs directory immediately
        pub.subscribe(self._add_run, "run_discovered")
        threading.Thread(target=find_runs_in_directory, kwargs={"directory":"/home/fbristow/Downloads/irida-sample-data"}).start()

    def _add_run(self, run):
        logging.info("Adding run [{}]".format(run.sample_sheet_dir))
        run_panel = RunPanel(self._run_panel, run)
        self._run_panel.Freeze()
        self._run_sizer.Add(run_panel, flag=wx.EXPAND)
        self._run_panel.Layout()
        self._run_panel.Thaw()

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

    def _open_about(self, evt):
        app_info = wx.AboutDialogInfo()
        app_info.Name = self._app_name
        app_info.Version = self._app_version
        app_info.WebSite = (self._app_url, "IRIDA Uploader on GitHub")
        app_info.Description = wordwrap("IRIDA Uploader is a tool to send Illumina MiSeq data to an instance of IRIDA for management.", 350, wx.ClientDC(self))

        wx.AboutBox(app_info)

    def _open_settings(self, evt):
        settings = SettingsFrame(self)
        settings.Show()
