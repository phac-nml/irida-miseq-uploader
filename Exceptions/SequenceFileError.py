class SequenceFileError(Exception):
    def __init__(self, message, errors):
        self._message = message
        self._errors = errors

    @property
    def message(self):
        return self._message

    @property
    def errors(self):
        return self._errors

    def __str__(self):
        return self.message
