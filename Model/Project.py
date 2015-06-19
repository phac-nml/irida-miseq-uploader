class Project:

    def __init__(self, projectName, projectDescription=None, projectID=None):#projectID is optional because it's not necessary when creating a Project object to send.
    #projectID is the identifier key when getting projects from the API.

        self.projectName=projectName
        self.projectDescription=str(projectDescription)
        self.projectID=str(projectID)

    def getID(self):
        return self.projectID

    def getName(self):
        return self.projectName

    def getDescription(self):
        return self.projectDescription

    def getDict(self):#for sending
        return {"name":self.projectName, "projectDescription":self.projectDescription}

    def __str__(self):
        return "ID:" + self.projectID + " Name:" + self.projectName + " Description: " + self.projectDescription
