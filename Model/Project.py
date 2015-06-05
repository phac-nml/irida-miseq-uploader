class Project:

  def __init__(self, projectID, projectName, projectDescription=None):
    self.projectID=str(projectID)
    self.projectName=projectName
    self.projectDescription=str(projectDescription)

  def getID(self):
    return self.projectID

  def getName(self):
    return self.projectName

  def getDescription(self):
    return self.projectDescription

  def __str__(self):
    return "ID:" + self.projectID + " Name:" + self.projectName + " Description: " + self.projectDescription
