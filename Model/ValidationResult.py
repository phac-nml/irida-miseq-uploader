class ValidationResult():

    def __init__(self):
        self.valid = None
        self.errorMsgs = []

    def addErrorMsg(self, msg):
        self.errorMsgs.append(msg)

    def setValid(self, boolean):
        self.valid = boolean

    def isValid(self):
        return self.valid

    def errorCount(self):
        return len(self.errorMsgs)

    def getErrors(self):
        retVal = ""
        if len(self.errorMsgs) > 0:
            for errorMsg in self.errorMsgs:
                retVal = retVal + errorMsg + "\n"
        else:
            retVal = "No error messages"
        return retVal
