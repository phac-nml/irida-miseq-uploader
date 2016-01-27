#!/usr/bin/env python

import wx
import logging
import webbrowser
from github3 import GitHub
from wx.lib.dialogs import MultiMessageBox
import wx.lib.delayedresult as dr
from distutils.version import LooseVersion
import ConfigParser
from os import path

from GUI.MainFrame import MainFrame

path_to_module = path.dirname(__file__)
app_config = path.join(path_to_module, 'irida-uploader.cfg')
if not path.isfile(app_config):
    app_config = path.join(path_to_module, '..', 'irida-uploader.cfg')

class Uploader(wx.App):

    def __init__(self, redirect=False, filename=None):
        wx.App.__init__(self, redirect, filename)
        self.get_app_info()
        self.check_for_update()

        self.frame = MainFrame()
        self.frame.Show()
        self.frame.mp.api = self.frame.settings_frame.attempt_connect_to_api()

    def get_app_info(self):
        config_parser = ConfigParser.ConfigParser()
        config_parser.read(app_config)
        self.__version__ = config_parser.get('Application', 'version', None)

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
            release_url = "https://github.com/phac-nml/irida-miseq-uploader/releases/latest"
            if LooseVersion(self.__version__) < LooseVersion(latest_tag.name):
                logging.debug("Newer version found.")
                response = MultiMessageBox(
                    ("A new version of the IRIDA MiSeq "
                     "Uploader tool is available. You can"
                     " download the latest version from ") + release_url,
                    "IRIDA MiSeq Uploader update available",
                    style=wx.YES_NO,
                    btnLabels={wx.ID_YES: "Open download page in web browser",
                               wx.ID_NO: "Close"})
                if response == wx.YES:
                    wx.CallAfter(webbrowser.open, github_url)
            else:
                logging.debug("No new versions found.")

        dr.startWorker(handle_update, find_update)

def main():
    app = Uploader()
    app.MainLoop()

if __name__ == "__main__":
    main()
