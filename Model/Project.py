class Project:

    # project_id is optional because it's not necessary when creating a Project
    # object to send.
    def __init__(self, proj_name, proj_description=None, proj_id=None):
        # proj_id is the identifier key when getting projects from the API.

        self.project_name = proj_name
        self.project_description = str(proj_description)
        self.project_id = str(proj_id)

    def get_id(self):
        return self.project_id

    def get_name(self):
        return self.project_name

    def get_description(self):
        return self.project_description

    def get_dict(self):  # for sending
        return {"name": self.project_name,
                "projectDescription": self.project_description}

    def __str__(self):
        return "ID:" + self.project_id + " Name:" + self.project_name + \
            " Description: " + self.project_description
