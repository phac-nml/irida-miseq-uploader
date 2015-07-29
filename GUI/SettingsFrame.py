import wx
import sys
from os import path
from requests.exceptions import ConnectionError
from ConfigParser import RawConfigParser
from collections import OrderedDict
from wx.lib.agw.genericmessagedialog import GenericMessageDialog as GMD

from API.apiCalls import ApiCalls

path_to_module = path.dirname(__file__)
if len(path_to_module) == 0:
    path_to_module = '.'

DEFAULT_BASE_URL = "http://localhost:8080/api/"
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "password1"
DEFAULT_CLIENT_ID = "testClient"
DEFAULT_CLIENT_SECRET = "testClientSecret"


class SettingsPanel(wx.Panel):

    def __init__(self, parent):

        self.parent = parent
        self.WINDOW_SIZE = (700, 550)
        wx.Panel.__init__(self, parent)

        self.conf_parser = RawConfigParser()
        self.config_file = path_to_module + "/../config.conf"
        self.conf_parser.read(self.config_file)
        self.config_dict = OrderedDict()
        self.load_curr_config()
        self.prompt_dlg = None
        self.show_debug_msg = False

        self.SHORT_BOX_SIZE = (200, -1)  # user, pass, id, secret
        self.LABEL_TEXT_WIDTH = 70
        self.SIZER_BORDER = 5
        self.LOG_PANEL_SIZE = (self.WINDOW_SIZE[0]*0.95, 230)
        self.CREDENTIALS_CTNR_LOG_PNL_SPACE = 5
        self.LOG_PNL_REG_TXT_COLOR = wx.BLACK
        self.LOG_PNL_UPDATED_TXT_COLOR = wx.BLUE
        self.LOG_PNL_ERR_TXT_COLOR = wx.RED
        self.LOG_PNL_OK_TXT_COLOR = (0, 102, 0)  # dark green
        self.ICON_WIDTH = self.ICON_HEIGHT = 24
        self.CREDENTIALS_SPACE = 30
        self.PADDING_LEN = 5
        self.ICON_TXT_FIELD_SPACE = 5
        self.TEXTBOX_FONT = wx.Font(
            pointSize=10, family=wx.FONTFAMILY_DEFAULT,
            style=wx.FONTSTYLE_NORMAL, weight=wx.FONTWEIGHT_NORMAL)
        self.LABEL_TXT_FONT = self.TEXTBOX_FONT
        self.ERR_TXT_FONT = self.TEXTBOX_FONT

        self.padding = wx.BoxSizer(wx.VERTICAL)
        self.top_sizer = wx.BoxSizer(wx.VERTICAL)

        self.url_box_err_sizer = wx.BoxSizer(wx.VERTICAL)
        self.url_box_icon_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.url_container = wx.BoxSizer(wx.HORIZONTAL)

        self.user_pass_static_box = wx.StaticBox(
            self, label="User authorization")
        self.user_pass_static_box.SetFont(self.LABEL_TXT_FONT)
        self.user_pass_container = wx.StaticBoxSizer(
            self.user_pass_static_box, wx.VERTICAL)

        self.username_box_err_sizer = wx.BoxSizer(wx.VERTICAL)
        self.username_box_icon_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.username_container = wx.BoxSizer(wx.HORIZONTAL)

        self.password_box_err_sizer = wx.BoxSizer(wx.VERTICAL)
        self.password_box_icon_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.password_container = wx.BoxSizer(wx.HORIZONTAL)

        self.id_secret_static_box = wx.StaticBox(
            self, label="Client authorization")
        self.id_secret_static_box.SetFont(self.LABEL_TXT_FONT)
        self.id_secret_container = wx.StaticBoxSizer(
            self.id_secret_static_box, wx.VERTICAL)

        self.client_id_box_err_sizer = wx.BoxSizer(wx.VERTICAL)
        self.client_id_box_icon_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.client_id_container = wx.BoxSizer(wx.HORIZONTAL)

        self.client_secret_box_err_sizer = wx.BoxSizer(wx.VERTICAL)
        self.client_secret_box_icon_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.client_secret_container = wx.BoxSizer(wx.HORIZONTAL)

        self.credentials_container = wx.BoxSizer(wx.HORIZONTAL)

        self.debug_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.log_panel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.debug_log_container = wx.BoxSizer(wx.VERTICAL)

        self.progress_bar_sizer = wx.BoxSizer(wx.VERTICAL)

        self.buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.create_icon_images()
        self.add_URL_section()
        self.add_username_section()
        self.add_password_section()
        self.add_client_id_section()
        self.add_client_secret_section()
        self.add_debug_checkbox()
        self.add_log_panel_section()

        self.add_close_btn()

        self.SetSizer(self.padding)

        self.top_sizer.Add(self.url_container, proportion=1,
                           flag=wx.TOP | wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER |
                           wx.EXPAND, border=self.SIZER_BORDER*2)

        self.user_pass_container.Add(
            self.username_container, proportion=0,
            flag=wx.ALL, border=self.SIZER_BORDER)
        self.user_pass_container.Add(
            self.password_container, proportion=0,
            flag=wx.ALL, border=self.SIZER_BORDER)

        self.id_secret_container.Add(
            self.client_id_container, proportion=0,
            flag=wx.ALL, border=self.SIZER_BORDER)
        self.id_secret_container.Add(
            self.client_secret_container, proportion=0,
            flag=wx.ALL, border=self.SIZER_BORDER)

        self.credentials_container.Add(self.user_pass_container)
        self.credentials_container.AddSpacer(self.CREDENTIALS_SPACE)
        self.credentials_container.Add(self.id_secret_container)

        self.top_sizer.Add(
            self.credentials_container, proportion=0,
            flag=wx.ALIGN_CENTER | wx.BOTTOM, border=self.SIZER_BORDER*2)

        self.debug_log_container.Add(self.debug_sizer)
        self.debug_log_container.Add(self.log_panel_sizer)

        self.top_sizer.Add(
            self.debug_log_container, proportion=0,
            flag=wx.ALIGN_CENTER)

        self.padding.Add(self.top_sizer, flag=wx.ALL | wx.EXPAND,
                         border=self.PADDING_LEN)

        self.padding.AddStretchSpacer()
        self.padding.Add(
            self.buttons_sizer, flag=wx.ALIGN_BOTTOM | wx.EXPAND |
            wx.LEFT | wx.RIGHT | wx.BOTTOM, border=self.SIZER_BORDER*3)

        self.Center()
        self.Layout()

    def load_curr_config(self):

        """
        Read from config file and load baseURL, username, password, client ID
        and client secret in to self.config_dict

        no return value
        """

        self.config_dict["baseURL"] = self.conf_parser.get("apiCalls",
                                                           "baseURL")
        self.config_dict["username"] = self.conf_parser.get("apiCalls",
                                                            "username")
        self.config_dict["password"] = self.conf_parser.get("apiCalls",
                                                            "password")
        self.config_dict["client_id"] = self.conf_parser.get("apiCalls",
                                                             "client_id")
        self.config_dict["client_secret"] = self.conf_parser.get(
                                            "apiCalls", "client_secret")

    def create_api_obj(self):

        api = ApiCalls(self.config_dict["client_id"],
                       self.config_dict["client_secret"],
                       self.config_dict["baseURL"],
                       self.config_dict["username"],
                       self.config_dict["password"])

        return api

    def attempt_connect_to_api(self):

        """
        attempt to create a connection to api with saved config credentials

        return ApiCalls object created from self.create_api_obj
        """

        api = None

        try:

            api = self.create_api_obj()

            self.reset_display()

            self.log_color_print("\nSuccessfully connected to API.",
                                 self.LOG_PNL_OK_TXT_COLOR)

            self.show_success_icon(self.base_URL_icon)
            self.show_success_icon(self.username_icon)
            self.show_success_icon(self.password_icon)
            self.show_success_icon(self.client_id_icon)
            self.show_success_icon(self.client_secret_icon)

            self.Refresh()

        except ConnectionError, e:
            self.handle_URL_error(e)

        except KeyError, e:
            self.handle_key_error(e)

        except ValueError, e:
            self.handle_val_error(e)

        except:
            self.handle_unexpected_error()

        return api

    def handle_URL_error(self, e, msg_printed=False):

        """
        for handling ConnectionError when trying to connect to API
        can also be called inside handle_key_error() in which case this method
        won't print the message from server because it's already printed
        in handle_key_error()

        arguments:
            e -- the ConnectionError object
            msg_printed -- boolean for deciding whether or not to print msg

        no return value
        """

        if msg_printed is False:
            self.handle_showing_server_msg(e)

        err_description = ("Cannot connect to url: {url}\n".format(
                           url=self.base_URL_box.GetValue()))

        err_log_msgs = [err_description]

        err_labels = [self.url_err_label]
        err_boxes = [self.base_URL_box]
        err_icons = [self.base_URL_icon]
        icon_tooltip = (err_description +
                        ("\nCheck for typos and if the IRIDA " +
                         "web server is running."))

        self.display_gui_errors(err_labels, err_boxes, err_log_msgs,
                                err_description, err_icons,
                                icon_tooltip)

    def handle_key_error(self, e):

        """
        for handling KeyError when trying to connect to API
        KeyError is raised when a base_URL that doesn't have an /api is given
        which is why handle_URL_error() can be called in here

        arguments:
            e -- the KeyError object

        no return value
        """

        credentials_err = False

        if "Bad credentials" in str(e.message):

            err_description = "Username and/or password is incorrect."

            err_labels = [self.username_err_label, self.password_err_label]
            err_boxes = [self.username_box, self.password_box]

            err_icons = [self.username_icon, self.password_icon]
            icon_tooltip = (
                "The username and/or password you provided " +
                "is incorrect. We can't let you know which one is incorrect " +
                "for security reasons.")

            credentials_err = True

        elif "clientId does not exist" in str(e.message):

            err_description = "Client ID is incorrect."

            err_labels = [self.client_id_err_label]
            err_boxes = [self.client_id_box]

            err_icons = [self.client_id_icon]
            icon_tooltip = err_description

            credentials_err = True

        elif "Bad client credentials" in str(e.message):

            err_description = "Client Secret is incorrect."

            err_labels = [self.client_secret_err_label]
            err_boxes = [self.client_secret_box]

            err_icons = [self.client_secret_icon]
            icon_tooltip = err_description

            credentials_err = True
        #

        if credentials_err:
            err_log_msgs = ["Invalid credentials:", err_description]
            self.display_gui_errors(err_labels, err_boxes, err_log_msgs,
                                    err_description, err_icons, icon_tooltip)

        else:
            self.handle_URL_error(e, msg_printed=True)

        self.handle_showing_server_msg(e)

    def handle_val_error(self, e):

        """
        value error can be raised by enterring malformed url

        argument:
            e -- the ValueError object

        no return value
        """

        err_description = ("Cannot connect to url: {url}\n".format(
                           url=self.base_URL_box.GetValue()))

        err_log_msgs = [err_description,
                        "Value error message: " + str(e.message)]

        err_labels = [self.url_err_label]
        err_boxes = [self.base_URL_box]
        err_icons = [self.base_URL_icon]
        icon_tooltip = err_description

        self.display_gui_errors(err_labels, err_boxes, err_log_msgs,
                                err_description, err_icons,
                                icon_tooltip)

    def handle_unexpected_error(self):
        """
        for handling unexpected raised errors
        since there is no restriction on saving, it is possible that user input
        can cause an unknown error to be raised which will cause the program to
        crash.
        and because attempt_connect_to_api is always called when the
        program starts, that same unkown error will be continually raised
        until the credentials enterred are updated - which is not possible
        using the program because of the crashing so the only way that it can
        be changed is by editing to config file itself.

        catching all exceptions like this allows the program to be still
        opened even if the credentials enterred in a previous session raises an
        unkown error

        no return value
        """

        err_log_msgs = ["Unexpected error:", str(sys.exc_info())]
        self.display_gui_errors(err_log_msgs=err_log_msgs)

    def display_gui_errors(self, err_labels=[], err_boxes=[], err_log_msgs=[],
                           err_description="", err_icons=[],
                           icon_tooltip=""):
        """
        update gui to display errors

        arguments:
            err_labels -- list of label text objects to have their label set
                          to err_description
            err_boxes -- used to be: list of textbox objects to have their
                         background set to self.INVALID_CONNECTION_COLOR
                         currently isn't used
            err_log_msgs -- list of string messages to display to the log_panel
            err_description -- description of error to be used for err_labels
            err_icons -- list of icons to be changed to show warning icon
            icon_tooltip -- string message for the warning icons when hovered

        no return value
        """

        self.reset_display()

        for label in err_labels:
            label.SetLabel(err_description)

        for log_msg in err_log_msgs:
            self.log_color_print(log_msg,
                                 self.LOG_PNL_ERR_TXT_COLOR)

        for icon in err_icons:
            self.show_warning_icon(icon,
                                   tooltip=icon_tooltip)

    def reset_display(self):

        """
        set gui objects (box, label, icons) to initial state
        hide all error labels - set to empty string
        hide all icons - replace them with transparent icon
        """

        self.url_err_label.SetLabel("\n")
        self.username_err_label.SetLabel("")
        self.password_err_label.SetLabel("")
        self.client_id_err_label.SetLabel("")
        self.client_secret_err_label.SetLabel("")

        self.hide_icon(self.base_URL_icon, hide=True)
        self.hide_icon(self.password_icon)
        self.hide_icon(self.username_icon)
        self.hide_icon(self.client_id_icon)
        self.hide_icon(self.client_secret_icon)

    def add_URL_section(self):

        """
        Adds URL text label and text box in to panel
        Sets a tooltip when hovering over text label or text box describing
            the URL that needs to be entered in the text box

        no return value
        """

        self.base_url_label = wx.StaticText(
            parent=self, id=-1, size=(80, -1),
            label="Server URL")
        self.base_url_label.SetFont(self.LABEL_TXT_FONT)

        self.url_err_label = wx.StaticText(parent=self, id=-1, label="")
        self.url_err_label.SetFont(self.ERR_TXT_FONT)
        self.url_err_label.SetForegroundColour(self.LOG_PNL_ERR_TXT_COLOR)

        self.base_URL_box = wx.TextCtrl(self, size=(-1, self.ICON_HEIGHT),
                                        style=wx.TE_RICH)
        self.orig_URL = self.config_dict["baseURL"]
        self.base_URL_box.SetValue(self.orig_URL)
        self.base_URL_box.SetFont(self.TEXTBOX_FONT)
        self.base_URL_box.Bind(wx.EVT_KILL_FOCUS, self.save_changes)

        self.base_URL_icon = wx.StaticBitmap(self, bitmap=wx.EmptyBitmap(
            self.ICON_WIDTH, self.ICON_HEIGHT))

        tip = "Enter the URL for the IRIDA server"
        self.base_URL_box.SetToolTipString(tip)
        self.base_url_label.SetToolTipString(tip)

        self.url_box_icon_sizer.Add(self.base_url_label,
                                    flag=wx.ALIGN_CENTER_VERTICAL)
        self.url_box_icon_sizer.Add(self.base_URL_box, proportion=1,
                                    flag=wx.EXPAND)
        self.url_box_icon_sizer.Add(self.base_URL_icon,
                                    flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT,
                                    border=self.ICON_TXT_FIELD_SPACE)
        self.url_box_err_sizer.Add(self.url_box_icon_sizer, proportion=1,
                                   flag=wx.EXPAND)
        self.url_box_err_sizer.Add(self.url_err_label,
                                   flag=wx.ALIGN_CENTER)
        self.url_container.Add(self.url_box_err_sizer, proportion=1)

    def add_username_section(self):

        """
        Adds username text label, error text label and text box in to panel

        no return value
        """

        self.username_label = wx.StaticText(
            self, id=-1, label="Username", size=(self.LABEL_TEXT_WIDTH, -1))
        self.username_label.SetFont(self.LABEL_TXT_FONT)

        self.username_err_label = wx.StaticText(parent=self, id=-1, label="")
        self.username_err_label.SetFont(self.ERR_TXT_FONT)
        self.username_err_label.SetForegroundColour(self.LOG_PNL_ERR_TXT_COLOR)

        self.username_box = wx.TextCtrl(self, size=self.SHORT_BOX_SIZE)
        self.username_box.SetValue(self.config_dict["username"])
        self.username_box.SetFont(self.TEXTBOX_FONT)
        self.username_box.Bind(wx.EVT_KILL_FOCUS, self.save_changes)

        self.username_icon = wx.StaticBitmap(self, bitmap=wx.EmptyBitmap(
            self.ICON_WIDTH, self.ICON_HEIGHT))

        self.username_box_icon_sizer.Add(self.username_label,
                                         flag=wx.ALIGN_CENTER_VERTICAL)
        self.username_box_icon_sizer.Add(self.username_box)
        self.username_box_icon_sizer.Add(self.username_icon,
                                         flag=wx.ALIGN_CENTER_VERTICAL |
                                         wx.LEFT,
                                         border=self.ICON_TXT_FIELD_SPACE)
        self.username_box_err_sizer.Add(self.username_box_icon_sizer)
        self.username_box_err_sizer.Add(self.username_err_label,
                                        flag=wx.ALIGN_CENTER)
        self.username_container.Add(
            self.username_box_err_sizer, flag=wx.TOP,
            border=self.username_err_label.GetSize()[1])

    def add_password_section(self):

        """
        Adds password text label and text box in to panel

        no return value
        """

        self.password_label = wx.StaticText(
            self, id=-1, label="Password", size=(self.LABEL_TEXT_WIDTH, -1))
        self.password_label.SetFont(self.LABEL_TXT_FONT)

        self.password_err_label = wx.StaticText(self, id=-1, label="")
        self.password_err_label.SetFont(self.ERR_TXT_FONT)
        self.password_err_label.SetForegroundColour(self.LOG_PNL_ERR_TXT_COLOR)

        self.password_box = wx.TextCtrl(
            self, size=self.SHORT_BOX_SIZE, style=wx.TE_PASSWORD)
        self.password_box.SetValue(self.config_dict["password"])
        self.password_box.SetFont(self.TEXTBOX_FONT)
        self.password_box.Bind(wx.EVT_KILL_FOCUS, self.save_changes)

        self.password_icon = wx.StaticBitmap(self, bitmap=wx.EmptyBitmap(
            self.ICON_WIDTH, self.ICON_HEIGHT))

        self.password_box_icon_sizer.Add(self.password_label,
                                         flag=wx.ALIGN_CENTER_VERTICAL)
        self.password_box_icon_sizer.Add(self.password_box)
        self.password_box_icon_sizer.Add(self.password_icon,
                                         flag=wx.ALIGN_CENTER_VERTICAL |
                                         wx.LEFT,
                                         border=self.ICON_TXT_FIELD_SPACE)
        self.password_box_err_sizer.Add(self.password_box_icon_sizer)
        self.password_box_err_sizer.Add(self.password_err_label,
                                        flag=wx.ALIGN_CENTER)
        self.password_container.Add(self.password_box_err_sizer)

    def add_client_id_section(self):

        """
        Adds client ID text label and text box in to panel

        no return value
        """

        self.client_id_label = wx.StaticText(
            parent=self, id=-1, label="ID", size=(self.LABEL_TEXT_WIDTH, -1))
        self.client_id_label.SetFont(self.LABEL_TXT_FONT)

        self.client_id_err_label = wx.StaticText(self, id=-1, label="")
        self.client_id_err_label.SetFont(self.ERR_TXT_FONT)
        self.client_id_err_label.SetForegroundColour(
            self.LOG_PNL_ERR_TXT_COLOR)

        self.client_id_box = wx.TextCtrl(self, size=self.SHORT_BOX_SIZE)
        self.client_id_box.SetValue(self.config_dict["client_id"])
        self.client_id_box.SetFont(self.TEXTBOX_FONT)
        self.client_id_box.Bind(wx.EVT_KILL_FOCUS, self.save_changes)

        self.client_id_icon = wx.StaticBitmap(self, bitmap=wx.EmptyBitmap(
            self.ICON_WIDTH, self.ICON_HEIGHT))

        self.client_id_box_icon_sizer.Add(self.client_id_label,
                                          flag=wx.ALIGN_CENTER_VERTICAL)
        self.client_id_box_icon_sizer.Add(self.client_id_box)
        self.client_id_box_icon_sizer.Add(self.client_id_icon,
                                          flag=wx.ALIGN_CENTER_VERTICAL |
                                          wx.LEFT,
                                          border=self.ICON_TXT_FIELD_SPACE)
        self.client_id_box_err_sizer.Add(self.client_id_box_icon_sizer)
        self.client_id_box_err_sizer.Add(self.client_id_err_label,
                                         flag=wx.ALIGN_CENTER)
        self.client_id_container.Add(
            self.client_id_box_err_sizer, flag=wx.TOP,
            border=self.client_id_err_label.GetSize()[1])

    def add_client_secret_section(self):

        """
        Adds client secret text label and text box in to panel

        no return value
        """

        self.client_secret_label = wx.StaticText(
            self, id=-1, label="Secret", size=(self.LABEL_TEXT_WIDTH, -1))
        self.client_secret_label.SetFont(self.LABEL_TXT_FONT)

        self.client_secret_err_label = wx.StaticText(self, id=-1, label="")
        self.client_secret_err_label.SetFont(self.ERR_TXT_FONT)
        self.client_secret_err_label.SetForegroundColour(
            self.LOG_PNL_ERR_TXT_COLOR)

        self.client_secret_box = wx.TextCtrl(self, size=self.SHORT_BOX_SIZE)
        self.client_secret_box.SetValue(self.config_dict["client_secret"])
        self.client_secret_box.SetFont(self.TEXTBOX_FONT)
        self.client_secret_box.Bind(wx.EVT_KILL_FOCUS, self.save_changes)

        self.client_secret_icon = wx.StaticBitmap(self, bitmap=wx.EmptyBitmap(
            self.ICON_WIDTH, self.ICON_HEIGHT))

        self.client_secret_box_icon_sizer.Add(self.client_secret_label,
                                              flag=wx.ALIGN_CENTER_VERTICAL)
        self.client_secret_box_icon_sizer.Add(self.client_secret_box)
        self.client_secret_box_icon_sizer.Add(self.client_secret_icon,
                                              flag=wx.ALIGN_CENTER_VERTICAL |
                                              wx.LEFT,
                                              border=self.ICON_TXT_FIELD_SPACE)
        self.client_secret_box_err_sizer.Add(self.client_secret_box_icon_sizer)
        self.client_secret_box_err_sizer.Add(self.client_secret_err_label,
                                             flag=wx.ALIGN_CENTER)
        self.client_secret_container.Add(self.client_secret_box_err_sizer)

    def add_debug_checkbox(self):

        """
        Adds checkbox for debugging option which will display messages from
        the server in to the log panel

        no return value
        """

        self.debug_checkbox = wx.CheckBox(parent=self, id=-1,
                                          label="Show messages from server")
        self.debug_checkbox.Bind(wx.EVT_CHECKBOX, self.handle_debug_checkbox)
        self.debug_sizer.Add(self.debug_checkbox)

    def create_icon_images(self):

        """
        Creates success and warning icons to be used by show_warning_icon()
        and show_success_icon() when they are going to display an icon

        no return value
        """

        # success icon made by Google @ "http://www.google.com". CC BY 3.0
        suc_img_path = path.join(path_to_module, "images", "Success.png")
        self.suc_img = wx.Image(suc_img_path,
                                wx.BITMAP_TYPE_ANY).ConvertToBitmap()

        # warning icon made by Freepik @ "http://www.freepik.com". CC BY 3.0
        warn_img_path = path.join(path_to_module, "images", "Warning.png")
        self.warn_img = wx.Image(warn_img_path,
                                 wx.BITMAP_TYPE_ANY).ConvertToBitmap()

        placeholder_img_path = path.join(path_to_module, "images",
                                         "Placeholder.png")
        self.ph_img = wx.Image(placeholder_img_path,
                               wx.BITMAP_TYPE_ANY).ConvertToBitmap()

    def show_warning_icon(self, targ, tooltip=""):

        """
        inserts warning icon (self.warn_img) in to targs icon placeholder

        arguments:
            targ -- the icon place holder(s) to be shown
                    (e.g self.base_URL_icon)

            tooltip -- message to be used as a tooltip

        no return value
        """

        targ.SetBitmap(self.warn_img)
        if len(tooltip) > 0:
            targ.SetToolTipString(tooltip)
        targ.SetLabel("warning")  # for tests
        targ.Show()

        self.Layout()
        self.Refresh()

    def show_success_icon(self, targ, tooltip=""):

        """
        inserts success icon (self.suc_img) in to targ icon place holder

        arguments:
            targ -- the icon place holder to be shown (e.g self.base_URL_icon)
            tooltip -- message to be used as a tooltip

        no return value
        """

        targ.SetBitmap(self.suc_img)
        targ.SetToolTipString(tooltip)
        targ.SetLabel("success")  # for tests
        targ.Show()

        self.Layout()
        self.Refresh()

    def hide_icon(self, targ, hide=False):

        """
        hide icon for given targ

        arguments:
            targ -- the icon place holder to be hidden (e.g self.base_URL_icon)
            hide -- if True actually hide the icon object instead of placing
                    a transparent placeholder icon in it
                    used just for base_URL_icon because it's box expands

        no return value
        """
        if hide:
            targ.Hide()
        else:
            targ.SetBitmap(self.ph_img)
        targ.SetLabel("hidden")  # for tests
        self.Layout()
        self.Refresh()

    def handle_debug_checkbox(self, evt):

        """
        Funtion bound to self.debug_checkbox being clicked

        no return value
        """

        if self.debug_checkbox.IsChecked():
            self.show_debug_msg = True
        else:
            self.show_debug_msg = False

    def add_log_panel_section(self):

        """
        Adds log panel text control for displaying progress and errors

        no return value
        """

        self.log_panel = wx.TextCtrl(
            self, id=-1, value="",
            size=(self.LOG_PANEL_SIZE),
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH)
        value = ("Settings menu.\n" +
                 "Click 'Save' to keep any changes you make.\n" +
                 "Click 'Close' to go back to uploader window.\n" +
                 "Click 'Default' to restore settings to default values.\n")

        self.log_panel.SetFont(self.TEXTBOX_FONT)
        self.log_panel.SetForegroundColour(self.LOG_PNL_REG_TXT_COLOR)
        self.log_panel.AppendText(value)
        self.log_panel.AppendText("\n")
        self.log_panel_sizer.Add(self.log_panel)

    def print_config_to_log_panel(self, changes_dict):

        """
        prints config_dict key and value pairs
        if config_dict[key] is different from changes_dict[key] then
        print it in a different color set by `self.LOG_PNL_UPDATED_TXT_COLOR`

        arguments:
            changes_dict -- dictionary containing difference between
                            self.config_dict and values in config boxes

        no return value
        """

        for key in self.config_dict.keys():

            if key == "password":
                msg = "{key} = {asterisks} \n".\
                    format(key=key, asterisks=len(self.config_dict[key])*"*")
            else:
                msg = "{key} = {key_value} \n".\
                    format(key=key, key_value=self.config_dict[key])

            if key in changes_dict:
                self.log_color_print(msg, self.LOG_PNL_UPDATED_TXT_COLOR,
                                     add_new_line=False)
            else:
                self.log_panel.AppendText(msg)

        self.log_panel.AppendText("\n")

    def save_changes(self, evt):

        """
        Save data from config boxes that have been changed in to config file.
        Display saved config in log panel.

        no return value
        """

        changes_dict = self.get_changes_dict()
        if len(changes_dict) > 0:
            self.log_panel.Clear()
            self.log_panel.AppendText("Saving...\n")

            targ_section = "apiCalls"
            self.write_config_data(targ_section, changes_dict)

            self.load_curr_config()
            self.print_config_to_log_panel(changes_dict)

            self.attempt_connect_to_api()

    def add_close_btn(self):

        """
        Add close button. Clicking it will call close_handler().

        no return value
        """

        self.close_btn = wx.Button(self, label="Close")
        self.close_btn.Bind(wx.EVT_BUTTON, self.close_handler)
        self.buttons_sizer.AddStretchSpacer()
        self.buttons_sizer.Add(self.close_btn, flag=wx.ALIGN_RIGHT)

    def close_handler(self, event):

        """
        Function bound to window/SettingsFrame being closed
            (close button/alt+f4)
        Destroy self if running alone or hide self if running
            attached to iridaUploaderMain
        Check if any changes have been made that weren't saved and prompt user
        if they want to save them.

        no return value
        """

        changes_dict = self.get_changes_dict()

        if len(changes_dict) > 0:
            changes_str = ""
            for item in changes_dict.items():
                if item[0] == "password":
                    changes_str += ("password = {asterisk_str}".format(
                                    asterisk_str=len(item[1]) * "*") + "\n")
                else:
                    changes_str += " = ".join(item) + "\n"

            dlg_msg = ("You have unsaved changes:\n" + changes_str + "\n" +
                       "Save changes?")

            self.prompt_dlg = GMD(self, message=dlg_msg,
                                  caption="Unsaved changes!",
                                  agwStyle=wx.YES_NO | wx.YES_DEFAULT |
                                  wx.ICON_EXCLAMATION)
            self.prompt_dlg.Message = dlg_msg  # for test purposes only

            user_choice = self.prompt_dlg.ShowModal()
            if user_choice == wx.ID_YES:
                targ_section = "apiCalls"
                self.write_config_data(targ_section, changes_dict)
                self.load_curr_config()

            else:
                self.base_URL_box.SetValue(self.config_dict["baseURL"])
                self.username_box.SetValue(self.config_dict["username"])
                self.password_box.SetValue(self.config_dict["password"])
                self.client_id_box.SetValue(self.config_dict["client_id"])
                self.client_secret_box.SetValue(
                    self.config_dict["client_secret"])

                self.prompt_dlg.Destroy()

        if self.parent.parent is None:  # standalone
            self.parent.Destroy()

        else:
            self.parent.Hide()  # running attached to iridaUploaderMain

        self.log_panel.Clear()
        self.attempt_connect_to_api()

    def log_color_print(self, msg, color, add_new_line=True):

        """
        print colored text to the log_panel

        arguments:
            msg -- the message to print
            color -- the color to print the message in

        no return value
        """

        text_attrib = wx.TextAttr(color)

        start_color = len(self.log_panel.GetValue())
        end_color = start_color + len(msg)

        self.log_panel.AppendText(msg)
        self.log_panel.SetStyle(start_color, end_color, text_attrib)
        if add_new_line:
            self.log_panel.AppendText("\n")

    def get_changes_dict(self):

        """
        get the difference between what's currently in the base_URL, username,
            password, client id and client secret boxes compared to their
            values in self.config_dict

        returns dictionary containing only the differences between box values
            and config_dict
        """

        box_val_dict = self.get_curr_box_values()
        changes_dict = {key: str(box_val_dict[key])
                        for key in self.config_dict.keys()
                        if self.config_dict[key] != box_val_dict[key]}

        return changes_dict

    def get_curr_box_values(self):

        """
        Get current values in the textboxes/TextCtrl relating to config data
        and store them in val_dict

        return val_dict
        """

        val_dict = {}
        val_dict["baseURL"] = self.base_URL_box.GetValue()
        val_dict["username"] = self.username_box.GetValue()
        val_dict["password"] = self.password_box.GetValue()
        val_dict["client_id"] = self.client_id_box.GetValue()
        val_dict["client_secret"] = self.client_secret_box.GetValue()

        return val_dict

    def write_config_data(self, targ_section, new_config_data_dict):

        """
        write to config file: update values based on new_config_data_dict
        in the targ_section

        arguments:
            targ_section -- the section in the config file to update
            new_config_data_dict -- dict containing which config data to change
                                    and what values to replace them

        no return value
        """

        for key in new_config_data_dict.keys():
            self.conf_parser.set(targ_section, key, new_config_data_dict[key])

        with open(self.config_file, 'wb') as configfile:
            self.conf_parser.write(configfile)

    def handle_showing_server_msg(self, err):

        if self.show_debug_msg:
            self.log_color_print("Message from server: " + str(err.message),
                                 self.LOG_PNL_ERR_TXT_COLOR)


class SettingsFrame(wx.Frame):

    def __init__(self, parent=None):

        self.WINDOW_SIZE = (700, 550)
        self.parent = parent
        wx.Frame.__init__(self, parent=self.parent, id=wx.ID_ANY,
                          title="Settings",
                          size=self.WINDOW_SIZE,
                          style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^
                          wx.MAXIMIZE_BOX)

        self.sf = SettingsPanel(self)
        self.Center()
        self.attempt_connect_to_api = self.sf.attempt_connect_to_api
        self.Bind(wx.EVT_CLOSE, self.sf.close_handler)
        self.close_btn = self.sf.close_btn  # test_iridaUploaderMain.py


if __name__ == "__main__":
    app = wx.App(False)
    frame = SettingsFrame()
    frame.Show()
    frame.attempt_connect_to_api()
    app.MainLoop()
