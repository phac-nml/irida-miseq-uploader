import wx
from os import path
from ConfigParser import RawConfigParser

path_to_module = path.dirname(__file__)
if len(path_to_module) == 0:
    path_to_module = '.'


class SettingsPanel(wx.Panel):

    def __init__(self, parent=None):

        self.parent = parent
        wx.Panel.__init__(self, parent)

        self.conf_parser = RawConfigParser()
        self.config_file = path_to_module + "/../config.conf"
        self.conf_parser.read(self.config_file)
        self.p_bar_percent = 0

        self.LONG_BOX_SIZE = (400, 32)  # url and directories
        self.SHORT_BOX_SIZE = (200, 32)  # user and pass
        self.LABEL_TEXT_WIDTH = 70
        self.LABEL_TEXT_HEIGHT = 32

        self.top_sizer = wx.BoxSizer(wx.VERTICAL)
        self.url_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.user_pass_container = wx.BoxSizer(wx.VERTICAL)
        self.username_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.password_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.user_pass_client_secret_container = wx.BoxSizer(wx.HORIZONTAL)
        self.log_panel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.progress_bar_sizer = wx.BoxSizer(wx.VERTICAL)

        self.add_URL_section()
        self.add_username_section()
        self.add_password_section()
        self.add_log_panel_section()

        self.top_sizer.AddSpacer(30)

        self.top_sizer.Add(self.url_sizer, proportion=0, flag=wx.ALL, border=5)

        self.user_pass_container.Add(
            self.username_sizer, proportion=0, flag=wx.ALL, border=5)
        self.user_pass_container.Add(
            self.password_sizer, proportion=0, flag=wx.ALL, border=5)

        self.user_pass_client_secret_container.Add(
            self.user_pass_container, proportion=0, flag=wx.ALL, border=5)

        self.top_sizer.Add(
            self.user_pass_client_secret_container, proportion=0,
            flag=wx.ALL, border=5)

        self.top_sizer.Add(
            self.log_panel_sizer, proportion=0, flag=wx.ALL | wx.ALIGN_CENTER)

        self.top_sizer.AddStretchSpacer()

        self.top_sizer.Add(
            self.progress_bar_sizer, proportion=0,
            flag=wx.ALL | wx.ALIGN_CENTER, border=5)

        self.top_sizer.AddStretchSpacer()

        self.SetSizer(self.top_sizer)
        self.Layout()

    def add_URL_section(self):

        """
        Adds URL text label and text box in to panel
        Sets a tooltip when hovering over text label or text box describing
            the URL that needs to be entered in the text box

        no return value
        """

        self.base_URL_label = wx.StaticText(
            parent=self, id=-1,
            size=(self.LABEL_TEXT_WIDTH, self.LABEL_TEXT_HEIGHT),
            label="Base URL")
        self.base_URL_box = wx.TextCtrl(self, size=self.LONG_BOX_SIZE)
        self.prev_URL = self.conf_parser.get("iridaUploader", "baseURL")
        self.base_URL_box.SetValue(self.prev_URL)

        self.save_URL_checkbox = wx.CheckBox(
            parent=self, id=-1, label="Save URL for future use")
        if len(self.prev_URL) > 0:
            self.save_URL_checkbox.SetValue(True)
        else:
            self.save_URL_checkbox.SetValue(False)
        self.Bind(
            wx.EVT_CHECKBOX, self.url_checkbox_handler, self.save_URL_checkbox)

        self.url_sizer.Add(self.base_URL_label, 0, wx.ALL, 5)
        self.url_sizer.Add(self.base_URL_box, 0, wx.ALL, 5)
        self.url_sizer.Add(self.save_URL_checkbox, 0, wx.ALL, 5)

        tip = "Enter the URL for the IRIDA server"
        self.base_URL_box.SetToolTipString(tip)
        self.base_URL_label.SetToolTipString(tip)

    def url_checkbox_handler(self, event=""):

        """
        Function bound to url checkbox being clicked.
        If the checkbox is checked then save the url currently in the
            baseUrlBox to the config file
        If the checkbox is unchecked then write back the original
            value of baseURL.
        """

        if self.save_URL_checkbox.IsChecked():
            self.conf_parser.set(
                "iridaUploader", "baseURL", self.base_URL_box.GetValue())

        else:
            self.conf_parser.set("iridaUploader", "baseURL", self.prev_URL)

        with open(self.config_file, 'wb') as configfile:
            self.conf_parser.write(configfile)

    def add_username_section(self):

        """
        Adds username text label and text box in to panel

        no return value
        """

        self.username_label = wx.StaticText(
            parent=self, id=-1,
            size=(self.LABEL_TEXT_WIDTH, self.LABEL_TEXT_HEIGHT),
            label="Username")
        self.username_box = wx.TextCtrl(self, size=self.SHORT_BOX_SIZE)
        self.username_sizer.Add(self.username_label)
        self.username_sizer.Add(self.username_box)

    def add_password_section(self):

        """
        Adds password text label and text box in to panel

        no return value
        """

        self.password_label = wx.StaticText(
            self, id=-1,
            size=(self.LABEL_TEXT_WIDTH, self.LABEL_TEXT_HEIGHT),
            label="Password")
        self.password_box = wx.TextCtrl(
            self, size=self.SHORT_BOX_SIZE, style=wx.TE_PASSWORD)
        self.password_sizer.Add(self.password_label)
        self.password_sizer.Add(self.password_box)

    def add_log_panel_section(self):

        """
        Adds log panel text control for displaying progress and errors

        no return value
        """

        self.log_panel = wx.TextCtrl(
            self, id=-1,
            value="Settings menu.\n" +
                  "Click 'Save' to keep any changes you make.\n" +
                  "Click 'Cancel' to ignore changes.\n" +
                  "Click 'Default' to restore settings to default values.\n",
            size=(self.parent.WINDOW_SIZE[0]*0.95, 200),
            style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.log_panel_sizer.Add(self.log_panel)


class MainFrame(wx.Frame):

    def __init__(self):
        self.WINDOW_SIZE = (700, 500)
        wx.Frame.__init__(self, parent=None, id=wx.ID_ANY,
                          title="SettingsPanel",
                          size=self.WINDOW_SIZE,
                          style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^
                          wx.MAXIMIZE_BOX)
        # use default frame style but disable border resize and maximize

        self.sp = SettingsPanel(self)
        self.Center()
        self.Show()


if __name__ == "__main__":
    app = wx.App(False)
    frame = MainFrame()
    frame.Show()
    app.MainLoop()

'''
if __name__ == "__main__":
    app = wx.App(False)
    sp = SettingsPanel()
    sp.Show()
    app.MainLoop()
'''
