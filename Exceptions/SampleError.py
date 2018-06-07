class SampleError(Exception):
    """An exception to be raised when issues with samples arise.

    Examples include when IRIDA responds with an error during sample creation,
    or when the parsing component can't parse the sample section of the sample
    sheet.
    """
    def __init__(self, message, errors):
        """Initialize a SampleError.

        Args:
            message: the summary message that's causing the error.
            errors: a more detailed list of errors.
        """
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
