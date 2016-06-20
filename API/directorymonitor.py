import os
import logging

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from API.pubsub import send_message
from API.directoryscanner import find_runs_in_directory

class DirectoryMonitorTopics(object):
    new_run_observed = "new_run_observed"
    finished_discovering_run = "finished_discovering_run"

class CompletedJobInfoEventHandler(FileSystemEventHandler):
    def on_created(self, event):
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

def monitor_directory(directory):
    logging.info("Getting ready to monitor directory {}".format(directory))
    event_handler = CompletedJobInfoEventHandler()
    observer = Observer()
    observer.schedule(event_handler, directory, recursive=True)
    observer.start()
