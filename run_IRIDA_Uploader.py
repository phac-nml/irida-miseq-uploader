#!/usr/bin/env python

import wx
import logging
import webbrowser
from github3 import GitHub
from wx.lib.dialogs import MultiMessageBox
import wx.lib.delayedresult as dr
from distutils.version import LooseVersion

from GUI.MainFrame import MainFrame

class Uploader(wx.App):
    __version__="1.4.0-SNAPSHOT"

    def __init__(self, redirect=False, filename=None):
        wx.App.__init__(self, redirect, filename)
        self.check_for_update()

        self.frame = MainFrame()
        self.frame.Show()
        self.frame.mp.api = self.frame.settings_frame.attempt_connect_to_api()

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
            logging.debug("Found some updates?")
            latest_tag = result.get()
            logging.debug("Found update: [{}]".format(latest_tag))
            github_url = "https://github.com/phac-nml/irida-miseq-uploader/releases/latest"
            if LooseVersion(self.__version__) < LooseVersion(latest_tag.name):
                logging.debug("Newer version found.")
                response = MultiMessageBox(
                    ("A new version of the IRIDA MiSeq "
                     "Uploader tool is available. You can"
                     " download the latest version from ") + github_url,
                    "IRIDA MiSeq Uploader update available",
                    style=wx.YES_NO,
                    btnLabels={wx.ID_YES: "Open download page in web browser",
                               wx.ID_NO: "Close"})
                if response == wx.YES:
                    wx.CallAfter(webbrowser.open, github_url)

        dr.startWorker(handle_update, find_update)

def main():
    app = Uploader()
    app.MainLoop()

if __name__ == "__main__":
    main()
