import os
import logging

from wx.lib.pubsub import pub

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from API.pubsub import send_message
from API.directoryscanner import find_runs_in_directory
from GUI.SettingsDialog import SettingsDialog

class DirectoryMonitorTopics(object):
    """Topics for monitoring directories for new runs."""
    new_run_observed = "new_run_observed"
    finished_discovering_run = "finished_discovering_run"
    shut_down_directory_monitor = "shut_down_directory_monitor"

class CompletedJobInfoEventHandler(FileSystemEventHandler):
    """A subclass of watchdog.events.FileSystemEventHandler that will run
    a directory scan on the monitored directory. This will filter explicitly on
    a file creation event for a file with the name `CompletedJobInfo.xml`."""

    def on_created(self, event):
        """Overrides `on_created` in `FileSystemEventHandler` to filter on
        file creation events for `CompletedJobInfo.xml`."""

        if isinstance(event, FileCreatedEvent) and event.src_path.endswith('CompletedJobInfo.xml'):
            logging.info("Observed new run in {}, telling the UI to start uploading it.".format(event.src_path))
            directory = os.path.dirname(event.src_path)
            # tell the UI to clean itself up before observing new runs
            send_message(DirectoryMonitorTopics.new_run_observed)

            # this will send a bunch of events that the UI is listening for, but
            # unlike the UI (which runs this in a separate thread), we're going to do this
            # in our own thread and block on it so we can tell the UI to start
            # uploading once we've finished discovering the run
            find_runs_in_directory(directory)

            # now tell the UI to start
            send_message(DirectoryMonitorTopics.finished_discovering_run)
        else:
            logging.debug("Ignoring file event [{}] with path [{}]".format(str(event), event.src_path))

def monitor_directory(directory):
    """Starts monitoring the specified directory in a background thread. File events
    will be passed to the `CompletedJobInfoEventHandler`.

    Arguments:
        directory: the directory to monitor.
    """
    observer = Observer()

    logging.info("Getting ready to monitor directory {}".format(directory))
    event_handler = CompletedJobInfoEventHandler()
    observer.schedule(event_handler, directory, recursive=True)

    def stop_monitoring(*args, **kwargs):
        """Tells watchdog to stop watching the directory when the newly processed run
        was discovered."""
        logging.info("Halting monitoring on directory because run was discovered.")
        observer.stop()
        observer.join()

    pub.subscribe(stop_monitoring, SettingsDialog.settings_closed_topic)
    pub.subscribe(stop_monitoring, DirectoryMonitorTopics.new_run_observed)
    pub.subscribe(stop_monitoring, DirectoryMonitorTopics.shut_down_directory_monitor)

    observer.start()
