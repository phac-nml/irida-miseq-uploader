import wx
import webbrowser
import logging
from GUI.MainPanel import MainPanel
from os import path

path_to_module = path.dirname(__file__)

class MainFrame(wx.Frame):

    def __init__(self, parent=None):

        self.parent = parent
        self.display_size = wx.GetDisplaySize()
        self.num_of_monitors = wx.Display_GetCount()

        WIDTH_PCT = 0.85
        HEIGHT_PCT = 0.75
        self.WINDOW_SIZE_WIDTH = (
            self.display_size.x/self.num_of_monitors) * WIDTH_PCT
        self.WINDOW_SIZE_HEIGHT = (self.display_size.y) * HEIGHT_PCT

        self.WINDOW_MAX_WIDTH = 900
        self.WINDOW_MAX_HEIGHT = 800
        self.MIN_WIDTH_SIZE = 600
        self.MIN_HEIGHT_SIZE = 400
        if self.WINDOW_SIZE_WIDTH > self.WINDOW_MAX_WIDTH:
            self.WINDOW_SIZE_WIDTH = self.WINDOW_MAX_WIDTH
        if self.WINDOW_SIZE_HEIGHT > self.WINDOW_MAX_HEIGHT:
            self.WINDOW_SIZE_HEIGHT = self.WINDOW_MAX_HEIGHT

        self.WINDOW_SIZE = (self.WINDOW_SIZE_WIDTH, self.WINDOW_SIZE_HEIGHT)

        wx.Frame.__init__(self, parent=self.parent, id=wx.ID_ANY,
                          title="IRIDA Uploader",
                          size=self.WINDOW_SIZE,
                          style=wx.DEFAULT_FRAME_STYLE)

        self.mp = MainPanel(self)
        self.settings_frame = self.mp.settings_frame

        img_dir_path = path.join(path_to_module, "images")
        self.icon = wx.Icon(path.join(img_dir_path, "iu.ico"),
                            wx.BITMAP_TYPE_ICO)
        self.SetIcon(self.icon)

        self.add_menu()
        self.SetSizeHints(self.MIN_WIDTH_SIZE, self.MIN_HEIGHT_SIZE,
                          self.WINDOW_MAX_WIDTH, self.WINDOW_MAX_HEIGHT)
        self.Bind(wx.EVT_CLOSE, self.mp.close_handler)
        self.Center()

    def add_menu(self):

        """
        Adds Options menu on top of program
        Shortcut / accelerator: Alt + T

        no return value
        """

        self.menubar = wx.MenuBar()
        self.file_menu = wx.Menu()
        self.menubar.Append(self.file_menu, "&File")

        open_menu = self.file_menu.Append(wx.ID_PROPERTIES, "Settings")
        self.Bind(wx.EVT_MENU, self.open_settings, open_menu)

        docs_menu = self.file_menu.Append(wx.ID_HELP, "&Documentation")
        self.Bind(wx.EVT_MENU, self.open_docs, docs_menu)

        self.file_menu.AppendSeparator()

        exit_menu = self.file_menu.Append(wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, lambda evt: self.Destroy(), exit_menu)

        self.SetMenuBar(self.menubar)

    def open_settings(self, evt):

        """
        Open the settings menu(SettingsFrame)

        no return value
        """

        self.settings_frame.Center()
        self.settings_frame.Show()

    def open_docs(self, evt):

        """
        Open documentation with user's default browser

        no return value
        """
        docs_path = path.join(path_to_module, "..", "..", "html",
                              "index.html")
        logging.info(path_to_module)
        wx.CallAfter(webbrowser.open, docs_path)
