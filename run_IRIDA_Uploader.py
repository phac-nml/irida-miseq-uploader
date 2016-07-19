#!/usr/bin/env python

import wx
import logging
import webbrowser
import ConfigParser
import argparse
import wx.lib.delayedresult as dr
import wx.lib.agw.hyperlink as hl

from os import path, makedirs
from distutils.version import LooseVersion
from github3 import GitHub
from GUI import UploaderAppFrame, SettingsDialog
from appdirs import user_config_dir, user_log_dir
from wx.lib.pubsub import pub

path_to_module = path.dirname(__file__)
app_config = path.join(path_to_module, 'irida-uploader.cfg')
if not path.isfile(app_config):
    app_config = path.join(path_to_module, '..', 'irida-uploader.cfg')

if not path.exists(user_log_dir("iridaUploader")):
    makedirs(user_log_dir("iridaUploader"))

log_format = '%(asctime)s %(levelname)s\t%(filename)s:%(funcName)s:%(lineno)d - %(message)s'

logging.basicConfig(level=logging.DEBUG,
                    filename=path.join(user_log_dir("iridaUploader"), 'irida-uploader.log'),
                    format=log_format,
                    filemode='w')

console = logging.StreamHandler()
console.setFormatter(logging.Formatter(log_format))
logging.getLogger().addHandler(console)

class Uploader(wx.App):

    def __init__(self, show_new_ui=False, redirect=False, filename=None):
        wx.App.__init__(self, redirect, filename)
        self.get_app_info()
        self.check_for_update()

        user_config_file = path.join(user_config_dir("iridaUploader"), "config.conf")

        if not path.exists(user_config_file):
            dialog = SettingsDialog(first_run=True)
            dialog.ShowModal()

        self._show_main_app()

    def _show_main_app(self):
        frame = UploaderAppFrame(app_name=self.__app_name__, app_version=self.__app_version__, app_url=self.url)
        frame.Show()

    def get_app_info(self):
        config_parser = ConfigParser.ConfigParser()
        config_parser.read(app_config)
        self.__app_version__ = config_parser.get('Application', 'version', None)
        self.__app_name__ = config_parser.get('Application', 'name', None)

    @property
    def url(self):
        return "https://github.com/phac-nml/irida-miseq-uploader"

    def check_for_update(self):
        def find_update():
            logging.debug("Checking remote for new updates.")
            try:
                gh = GitHub()
                repo = gh.repository("phac-nml", "irida-miseq-uploader")
                # get the latest tag from github
                return next(repo.iter_tags(number=1))
            except:
                logging.warn("Couldn't reach github to check for new version.")
                raise

        def handle_update(result):
            latest_tag = result.get()
            logging.debug("Found latest version: [{}]".format(latest_tag))
            release_url = self.url + "/releases/latest"
            if LooseVersion(self.__app_version__) < LooseVersion(latest_tag.name):
                logging.info("Newer version found.")
                dialog = NewVersionMessageDialog(
                    parent=None,
                    id=wx.ID_ANY,
                    message=("A new version of the IRIDA MiSeq "
                     "Uploader tool is available. You can"
                     " download the latest version from "),
                    title="IRIDA MiSeq Uploader update available",
                    download_url=release_url,
                    style=wx.CAPTION|wx.CLOSE_BOX|wx.STAY_ON_TOP)
                dialog.ShowModal()
                dialog.Destroy()
            else:
                logging.debug("No new versions found.")

        dr.startWorker(handle_update, find_update)

class NewVersionMessageDialog(wx.Dialog):
    def __init__(self, parent, id, title, message, download_url, size=wx.DefaultSize, pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE, name='dialog'):
        wx.Dialog.__init__(self, parent, id, title, pos, size, style, name)

        label = wx.StaticText(self, label=message)
        button = wx.Button(self, id=wx.ID_OK, label="Close")
        button.SetDefault()

        line = wx.StaticLine(self, wx.ID_ANY, size=(20, -1), style=wx.LI_HORIZONTAL)
        download_ctrl = hl.HyperLinkCtrl(self, wx.ID_ANY, download_url, URL=download_url)

        sizer = wx.BoxSizer(wx.VERTICAL)
        button_sizer = wx.StdDialogButtonSizer()
        button_sizer.AddButton(button)
        button_sizer.Realize()

        sizer.Add(label, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        sizer.Add(download_ctrl, 0, wx.ALL, 10)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)
        sizer.Add(button_sizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)

def main():
    app = Uploader()
    app.MainLoop()

if __name__ == "__main__":
    main()
