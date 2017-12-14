import os
import logging
import time
import threading

from wx.lib.pubsub import pub

from API.pubsub import send_message
from API.directoryscanner import find_runs_in_directory
from GUI.SettingsDialog import SettingsDialog
from API.runuploader import RunUploaderTopics

toMonitor = True

class DirectoryMonitorTopics(object):
    """Topics for monitoring directories for new runs."""
    new_run_observed = "new_run_observed"
    finished_discovering_run = "finished_discovering_run"
    shut_down_directory_monitor = "shut_down_directory_monitor"
    start_up_directory_monitor = "start_up_directory_monitor"
    finished_uploading_run = "finished_uploading_run"

class RunMonitor(threading.Thread):

    def __init__(self, directory, cond, name="RunMonitorThread"):
        """Initialize a `RunMonitor`"""
        self._directory = directory
        self._condition = cond
        threading.Thread.__init__(self, name=name)

    def run(self):
        """Initiate directory monitor. The monitor checks the default 
        directory every 2 minutes
        """
        monitor_directory(self._directory,self._condition)

    def join(self, timeout=None):
        """Kill the thread"""
        global toMonitor
        logging.info("going to kill monitoring")
        toMonitor = False
        threading.Thread.join(self, timeout)



def on_created(directory, cond):
    """When a CompletedJobInfo.xml file is found without a .miseqUploaderInfo file,
    an automatic upload is triggered
    """
    logging.info("Observed new run in {}, telling the UI to start uploading it.".format(directory))
    directory = os.path.dirname(directory)
    # tell the UI to clean itself up before observing new runs
    send_message(DirectoryMonitorTopics.new_run_observed)
    logging.info("looking for runs in directory")
    if toMonitor:
        find_runs_in_directory(directory)
    if toMonitor:
        send_message(DirectoryMonitorTopics.finished_discovering_run)
        # using locks to prevent the monitor from running while an upload is happening.
        cond.acquire()
        cond.wait()
        cond.release()
        send_message(DirectoryMonitorTopics.finished_uploading_run)



def monitor_directory(directory, cond):
    """Calls the function searches the default directory every 2 minutes unless
    monitoring is no longer required
    """
    global toMonitor
    logging.info("Getting ready to monitor directory {}".format(directory))
    time.sleep(10)
    pub.subscribe(stop_monitoring, DirectoryMonitorTopics.shut_down_directory_monitor)
    pub.subscribe(start_monitoring, DirectoryMonitorTopics.start_up_directory_monitor)
    logging.info("Value of toMonitor {}".format(toMonitor))
    while toMonitor:
        search_for_upload(directory, cond)
        i = 0
        logging.info("Wait 2 minutes between monitoring unless monitoring shut down")        
        while toMonitor and i < 120:
            time.sleep(1)
            i = i+1
       

def search_for_upload(directory, cond):
    """loop through subdirectories of the default directory looking for CompletedJobInfo.xml without
    .miseqUploaderInfo files.
    """
    global toMonitor
    for root, dirs, files in os.walk(directory, topdown=True):
        for name in dirs:
            checkForCompJob = os.path.join(root, name, "CompletedJobInfo.xml")
            checkForMiSeq = os.path.join(root, name, ".miseqUploaderInfo")
            if os.path.isfile(checkForCompJob):
                if not os.path.isfile(checkForMiSeq):
                    path_to_upload = checkForCompJob
                    if toMonitor:
                        on_created(path_to_upload, cond)
                    # After upload, start back at the start of directories
                    return
            # Check each step of loop if monitoring is still required
            if not toMonitor:
                return
    return

def stop_monitoring(*args, **kwargs):
    """Stop directory monitoring by setting toMonitor to False"""
    global toMonitor
    logging.info("Halting monitoring on directory.")
    toMonitor = False

def start_monitoring():
    """Restart directory monitoring by setting toMonitor to True"""
    global toMonitor
    logging.info("Restarting monitor on directory")
    toMonitor = True
