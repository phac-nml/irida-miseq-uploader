from threading import Thread


class UploadThread(Thread):

    def __init__(self, command, *args):
        Thread.__init__(self)

        self.command = command
        self.args = args
        self.start()

    def run(self):

        self.thread = Thread(target=self.command, args=(self.args))
        self.thread.start()
        self.thread.join()

    def is_running(self):
        return self.thread.is_alive()
