import wx
import sys
from os import path
from requests.exceptions import ConnectionError
from ConfigParser import RawConfigParser
from collections import OrderedDict
from API.apiCalls import ApiCalls

path_to_module = path.dirname(__file__)
if len(path_to_module) == 0:
    path_to_module = '.'


class SettingsFrame(wx.Frame):

    def __init__(self, parent=None):

        self.parent = parent
        self.WINDOW_SIZE = (600, 500)
        wx.Frame.__init__(self, parent=None, id=wx.ID_ANY,
                          title="Settings",
                          size=self.WINDOW_SIZE,
                          style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^
                          wx.MAXIMIZE_BOX)

        self.conf_parser = RawConfigParser()
        self.config_file = path_to_module + "/../config.conf"
        self.conf_parser.read(self.config_file)
        self.config_dict = OrderedDict()
        self.load_curr_config()

        self.LONG_BOX_SIZE = (500, 32)  # url
        self.SHORT_BOX_SIZE = (200, 32)  # user, pass, id, secret
        self.LABEL_TEXT_WIDTH = 70
        self.LABEL_TEXT_HEIGHT = 32
        self.SIZER_BORDER = 5
        self.LOG_PANEL_SIZE = (self.WINDOW_SIZE[0]*0.95, 200)
        self.CREDENTIALS_CTNR_LOG_PNL_SPACE = 50
        self.LOG_PNL_REG_TXT_COLOR = wx.BLACK
        self.LOG_PNL_UPDATED_TXT_COLOR = wx.BLUE
        self.LOG_PNL_ERR_TXT_COLOR = wx.RED
        self.LOG_PNL_OK_TXT_COLOR = wx.GREEN
        self.VALID_CONNECTION_COLOR = (50, 255, 50)
        self.INVALID_CONNECTION_COLOR = (204, 0, 0)
        self.NEUTRAL_TXT_CTRL_COLOR = wx.WHITE

        self.top_sizer = wx.BoxSizer(wx.VERTICAL)
        self.url_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.user_pass_container = wx.BoxSizer(wx.VERTICAL)
        self.username_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.password_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.id_secret_container = wx.BoxSizer(wx.VERTICAL)
        self.client_id_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.client_secret_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.credentials_container = wx.BoxSizer(wx.HORIZONTAL)

        self.log_panel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.progress_bar_sizer = wx.BoxSizer(wx.VERTICAL)
        self.buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.add_URL_section()
        self.add_username_section()
        self.add_password_section()
        self.add_client_id_section()
        self.add_client_secret_section()
        self.add_log_panel_section()
        self.add_default_btn()
        self.add_save_btn()
        self.add_close_btn()

        self.SetSizer(self.top_sizer)

        self.top_sizer.Add(self.url_sizer, proportion=0,
                           flag=wx.ALL | wx.ALIGN_CENTER,
                           border=self.SIZER_BORDER)

        self.user_pass_container.Add(
            self.username_sizer, proportion=0,
            flag=wx.ALL, border=self.SIZER_BORDER)
        self.user_pass_container.Add(
            self.password_sizer, proportion=0,
            flag=wx.ALL, border=self.SIZER_BORDER)

        self.id_secret_container.Add(
            self.client_id_sizer, proportion=0,
            flag=wx.ALL, border=self.SIZER_BORDER)
        self.id_secret_container.Add(
            self.client_secret_sizer, proportion=0,
            flag=wx.ALL, border=self.SIZER_BORDER)

        self.credentials_container.Add(self.user_pass_container)
        self.credentials_container.Add(self.id_secret_container)

        spacer_size = (self.WINDOW_SIZE[0] -
                       self.credentials_container.GetMinSize()[0] -
                       (self.SIZER_BORDER*2))
        self.credentials_container.InsertSpacer(1, (spacer_size, -1))

        self.top_sizer.Add(
            self.credentials_container, proportion=0,
            flag=wx.ALL, border=self.SIZER_BORDER)

        self.top_sizer.AddSpacer(self.CREDENTIALS_CTNR_LOG_PNL_SPACE)
        self.top_sizer.Add(
            self.log_panel_sizer, proportion=0, flag=wx.ALL | wx.ALIGN_CENTER)

        self.Layout()

        button_spacing = (self.WINDOW_SIZE[0] -
                          (self.default_btn.GetSize()[0] +
                          self.save_btn.GetSize()[0] +
                          self.close_btn.GetSize()[0]) -
                          (self.SIZER_BORDER*2))
        self.buttons_sizer.InsertSpacer(1, button_spacing)

        space_bottom = (self.WINDOW_SIZE[1] -
                        (self.log_panel_sizer.GetPosition()[1] +
                         self.LOG_PANEL_SIZE[1] +
                         self.default_btn.GetSize()[1] + self.SIZER_BORDER))
        self.top_sizer.Add(
            self.buttons_sizer, proportion=0, flag=wx.TOP, border=space_bottom)

        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.close_handler)

    def load_curr_config(self):

        """
        Read from config file and load baseURL, username, password, client ID
        and client secret in to a config_dict

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

    def attempt_connect_to_api(self):

        """
        attempt to create a connection to api with saved config credentials

        no return value
        """

        try:
            ApiCalls(self.config_dict["client_id"],
                     self.config_dict["client_secret"],
                     self.config_dict["baseURL"],
                     self.config_dict["username"],
                     self.config_dict["password"])

            self.base_URL_box.SetBackgroundColour(self.VALID_CONNECTION_COLOR)
            self.username_box.SetBackgroundColour(self.VALID_CONNECTION_COLOR)
            self.password_box.SetBackgroundColour(self.VALID_CONNECTION_COLOR)
            self.client_id_box.SetBackgroundColour(self.VALID_CONNECTION_COLOR)
            self.client_secret_box.SetBackgroundColour(
                                                self.VALID_CONNECTION_COLOR)

            self.log_color_print("\nSuccessfully connected to API.\n",
                                 self.LOG_PNL_OK_TXT_COLOR)

        except ConnectionError, e:
            self.handle_URL_error(e)

        except KeyError, e:
            self.handle_key_error(e)

        except ValueError, e:
            self.log_color_print("Cannot connect to url:\n",
                                 self.LOG_PNL_ERR_TXT_COLOR)
            self.log_color_print("Value error message: " + str(e.message),
                                 self.LOG_PNL_ERR_TXT_COLOR)

        except:
            self.log_color_print("Unexpected error:" + "\n",
                                 self.LOG_PNL_ERR_TXT_COLOR)
            self.log_color_print(str(sys.exc_info())+"\n",
                                 self.LOG_PNL_ERR_TXT_COLOR)

        self.Refresh()

    def handle_URL_error(self, e, msg_printed=False):

        self.log_color_print("Cannot connect to url:\n",
                             self.LOG_PNL_ERR_TXT_COLOR)
        if msg_printed is False:
            self.log_color_print("Message from server: " + str(e.message),
                                 self.LOG_PNL_ERR_TXT_COLOR)

        self.base_URL_box.SetBackgroundColour(self.INVALID_CONNECTION_COLOR)

    def handle_key_error(self, e):

        self.base_URL_box.SetBackgroundColour(self.NEUTRAL_TXT_CTRL_COLOR)
        self.username_box.SetBackgroundColour(self.NEUTRAL_TXT_CTRL_COLOR)
        self.password_box.SetBackgroundColour(self.NEUTRAL_TXT_CTRL_COLOR)
        self.client_id_box.SetBackgroundColour(self.NEUTRAL_TXT_CTRL_COLOR)
        self.client_secret_box.SetBackgroundColour(self.NEUTRAL_TXT_CTRL_COLOR)

        self.log_color_print("Invalid credentials:\n",
                             self.LOG_PNL_ERR_TXT_COLOR)

        if "Bad credentials" in str(e.message):
            self.log_color_print("Username or password is incorrect.\n",
                                 self.LOG_PNL_ERR_TXT_COLOR)

            self.username_box.SetBackgroundColour(
                self.INVALID_CONNECTION_COLOR)

            self.password_box.SetBackgroundColour(
                self.INVALID_CONNECTION_COLOR)

        elif "clientId does not exist" in str(e.message):
            self.client_id_box.SetBackgroundColour(
                self.INVALID_CONNECTION_COLOR)

        elif "Bad client credentials" in str(e.message):
            self.client_secret_box.SetBackgroundColour(
                self.INVALID_CONNECTION_COLOR)

        elif "No client credentials were provided" in str(e.message):
            self.handle_URL_error(e, msg_printed=True)

        self.log_color_print("Message from server: " + str(e.message),
                             self.LOG_PNL_ERR_TXT_COLOR)

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
        self.orig_URL = self.config_dict["baseURL"]
        self.base_URL_box.SetValue(self.orig_URL)

        self.url_sizer.Add(self.base_URL_label, 0, wx.ALL, 5)
        self.url_sizer.Add(self.base_URL_box, 0, wx.ALL, 5)

        tip = "Enter the URL for the IRIDA server"
        self.base_URL_box.SetToolTipString(tip)
        self.base_URL_label.SetToolTipString(tip)

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
        self.username_box.SetValue(self.config_dict["username"])

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
        self.password_box.SetValue(self.config_dict["password"])

        self.password_sizer.Add(self.password_label)
        self.password_sizer.Add(self.password_box)

    def add_client_id_section(self):

        """
        Adds client ID text label and text box in to panel

        no return value
        """

        self.client_id_label = wx.StaticText(
            parent=self, id=-1,
            size=(self.LABEL_TEXT_WIDTH, self.LABEL_TEXT_HEIGHT),
            label="Client ID")

        self.client_id_box = wx.TextCtrl(self, size=self.SHORT_BOX_SIZE)
        self.client_id_box.SetValue(self.config_dict["client_id"])

        self.client_id_sizer.Add(self.client_id_label)
        self.client_id_sizer.Add(self.client_id_box)

    def add_client_secret_section(self):

        """
        Adds client secret text label and text box in to panel

        no return value
        """

        self.client_secret_label = wx.StaticText(
            self, id=-1,
            size=(self.LABEL_TEXT_WIDTH, self.LABEL_TEXT_HEIGHT),
            label="Client Secret")

        self.client_secret_box = wx.TextCtrl(self, size=self.SHORT_BOX_SIZE)
        self.client_secret_box.SetValue(self.config_dict["client_secret"])

        self.client_secret_sizer.Add(self.client_secret_label)
        self.client_secret_sizer.Add(self.client_secret_box)

    def add_log_panel_section(self):

        """
        Adds log panel text control for displaying progress and errors

        no return value
        """

        self.log_panel = wx.TextCtrl(
            self, id=-1, value="",
            size=(self.LOG_PANEL_SIZE),
            style=wx.TE_MULTILINE | wx.TE_READONLY)
        value = ("Settings menu.\n" +
                 "Click 'Save' to keep any changes you make.\n" +
                 "Click 'Close' to go back to uploader window.\n" +
                 "Click 'Default' to restore settings to default values.\n")

        self.log_panel.SetForegroundColour(self.LOG_PNL_REG_TXT_COLOR)
        self.log_panel.AppendText(value)
        self.log_panel_sizer.Add(self.log_panel)

    def add_default_btn(self):

        """
        Add default button. Clicking it will call restore_default_settings().

        no return value
        """

        self.default_btn = wx.Button(self, label="Restore to default")
        self.default_btn.Bind(wx.EVT_BUTTON, self.restore_default_settings)
        self.buttons_sizer.Add(self.default_btn, flag=wx.LEFT,
                               border=self.SIZER_BORDER)

    def restore_default_settings(self, evt):

        """
        Restore settings to their default values and write them to the
            config file
        call load_curr_config() to reload the config_dict and show their values
            in the log panel
        update config box values

        no return value
        """

        default_settings_dict = {}
        default_settings_dict["baseURL"] = "http://localhost:8080/api/"
        default_settings_dict["username"] = "admin"
        default_settings_dict["password"] = "password1"
        default_settings_dict["client_id"] = "testClient"
        default_settings_dict["client_secret"] = "testClientSecret"

        targ_section = "apiCalls"
        self.write_config_data(targ_section, default_settings_dict)

        self.load_curr_config()
        changes_dict = self.get_changes_dict()
        self.log_panel.AppendText("\nSettings restored to default values:\n")
        self.print_config_to_log_panel(changes_dict)

        self.base_URL_box.SetValue(default_settings_dict["baseURL"])
        self.username_box.SetValue(default_settings_dict["username"])
        self.password_box.SetValue(default_settings_dict["password"])
        self.client_id_box.SetValue(default_settings_dict["client_id"])
        self.client_secret_box.SetValue(default_settings_dict["client_secret"])

        self.attempt_connect_to_api()

    def print_config_to_log_panel(self, changes_dict):

        """
        prints config_dict key and value pairs
        if config_dict[key] is different from changes_dict[key] then
        print it in a different color set by `self.LOG_PNL_UPDATED_TXT_COLOR`

        no return value
        """

        for key in self.config_dict.keys():

            if key in changes_dict:
                self.log_panel.SetForegroundColour(
                    self.LOG_PNL_UPDATED_TXT_COLOR)

            self.log_panel.AppendText(key + " = " + self.config_dict[key])
            self.log_panel.AppendText("\n")

            self.log_panel.SetForegroundColour(self.LOG_PNL_REG_TXT_COLOR)

    def add_save_btn(self):

        """
        Adds save button. Clicking it will call save_changes().

        no return value
        """

        self.save_btn = wx.Button(self, label="Save")
        self.save_btn.Bind(wx.EVT_BUTTON, self.save_changes)
        self.buttons_sizer.Add(self.save_btn)

    def save_changes(self, evt):

        """
        Save data from config boxes that have been changed in to config file.
        Display saved config in log panel.

        no return value
        """

        changes_dict = self.get_changes_dict()
        if len(changes_dict) > 0:
            self.log_panel.AppendText("\nSaving...\n")

            targ_section = "apiCalls"
            self.write_config_data(targ_section, changes_dict)

            self.load_curr_config()
            self.print_config_to_log_panel(changes_dict)
        else:
            self.log_panel.SetForegroundColour(self.LOG_PNL_ERR_TXT_COLOR)
            self.log_panel.AppendText("No changes to save.\n")
            self.log_panel.SetForegroundColour(self.LOG_PNL_REG_TXT_COLOR)

        self.attempt_connect_to_api()

    def add_close_btn(self):

        """
        Add close button. Clicking it will call close_handler().

        no return value
        """

        self.close_btn = wx.Button(self, label="Close")
        self.close_btn.Bind(wx.EVT_BUTTON, self.close_handler)
        self.buttons_sizer.Add(self.close_btn)

    def close_handler(self, event):

        """
        Function bound to window/MainFrame being closed (close button/alt+f4)
        Destroy parent(MainFrame) to continue with regular closing procedure
        Check if any changes have been made that weren't saved and prompt user
        if they want to save them.

        no return value
        """

        changes_dict = self.get_changes_dict()

        if len(changes_dict) > 0:
            changes_str = ""
            for item in changes_dict.items():
                changes_str += " = ".join(item) + "\n"

            dlg_msg = ("You have unsaved changes:\n" + changes_str + "\n" +
                       "Save changes?")
            prompt_msg = wx.MessageDialog(self, dlg_msg,
                                          caption="Unsaved changes!",
                                          style=wx.YES_NO | wx.YES_DEFAULT |
                                          wx.STAY_ON_TOP |
                                          wx.ICON_EXCLAMATION)

            user_choice = prompt_msg.ShowModal()
            if user_choice == wx.ID_YES:
                targ_section = "apiCalls"
                self.write_config_data(targ_section, changes_dict)

            else:
                prompt_msg.Destroy()

        if self.parent is None:  # if running SettingsFrame by itself
            self.Destroy()
        else:
            self.Hide()  # running attached to iridaUploaderMain

    def log_color_print(self, msg, color):

        self.log_panel.SetForegroundColour(color)
        self.log_panel.AppendText(msg)
        self.log_panel.SetForegroundColour(self.LOG_PNL_REG_TXT_COLOR)

    def get_changes_dict(self):

        box_val_dict = self.get_curr_box_values()
        changes_dict = {key: str(box_val_dict[key])
                        for key in self.config_dict.keys()
                        if self.config_dict[key] != box_val_dict[key]}

        return changes_dict

    def get_curr_box_values(self):

        """
        Get current values in the textboxes/TextCtrl relating to config data
        and store them in val dict

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

        no return value
        """

        for key in new_config_data_dict.keys():
            self.conf_parser.set(targ_section, key, new_config_data_dict[key])

        with open(self.config_file, 'wb') as configfile:
            self.conf_parser.write(configfile)


if __name__ == "__main__":
    app = wx.App(False)
    frame = SettingsFrame()
    frame.Show()
    frame.attempt_connect_to_api()
    app.MainLoop()
