class SampleSheetError(Exception):
    """An exception raised when errors are encountered with a sample sheet.

    Examples include when a sample sheet can't be parsed because it's garbled, or
    if IRIDA rejects the creation of a run because fields are missing or invalid
    from the sample sheet.
    """
    def __init__(self, message, errors):
        """Initalize a SampleSheetError.

        Args:
            message: a summary message that's causing the error.
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
