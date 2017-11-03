import os
import logging
import time

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

def on_created(directory):
    logging.info("Observed new run in {}, telling the UI to start uploading it.".format(directory))
    directory = os.path.dirname(directory)
    # tell the UI to clean itself up before observing new runs
    send_message(DirectoryMonitorTopics.new_run_observed)
    # this will send a bunch of events that the UI is listening for, but
    # unlike the UI (which runs this in a separate thread), we're going to do this
    # in our own thread and block on it so we can tell the UI to start
    # uploading once we've finished discovering the run
    find_runs_in_directory(directory)
    # now tell the UI to start
    time.sleep(20)
    # logging.info("about to send message finished discovering run")
    send_message(DirectoryMonitorTopics.finished_discovering_run)


def monitor_directory(directory):
    global toMonitor
    logging.info("Getting ready to monitor directory {}".format(directory))
    # logging.info("Value of toMonitor {}".format(toMonitor))
    pub.subscribe(stop_monitoring, DirectoryMonitorTopics.new_run_observed)
    pub.subscribe(stop_monitoring, DirectoryMonitorTopics.shut_down_directory_monitor)
    pub.subscribe(start_monitoring, RunUploaderTopics.finished_uploading_samples)
    # logging.info("before if statement")
    while toMonitor:
        search_for_upload(directory)
        logging.info("after if statement")
        time.sleep(60)
    # logging.info("end of while loop")

def search_for_upload(directory):
    # logging.info("search for upload loops")
    for root, dirs, files in os.walk(directory, topdown=False):
        for name in dirs:
            # logging.info("dir searching {}".format(os.path.join(root, name)))
            checkForCompJob = os.path.join(root, name, "CompletedJobInfo.xml")
            checkForMiSeq = os.path.join(root, name, ".miseqUploaderInfo")
            if os.path.isfile(checkForCompJob):
                if not os.path.isfile(checkForMiSeq):
                    path_to_upload = checkForCompJob
                    # logging.info("Observed new run in {}".format(path_to_upload))
                    on_created(path_to_upload)
                    # logging.info("Returning from search by breaking loops")
                    return
    return

def stop_monitoring(*args, **kwargs):
    global toMonitor
    logging.info("Halting monitoring on directory.")
    toMonitor = False

def start_monitoring():
    global toMonitor
    logging.info("Restarting monitor on directory")
    toMonitor = True
