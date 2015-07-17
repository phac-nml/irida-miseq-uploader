def project_exists(api, project_id):

    proj_list = api.get_projects()

    if any([proj.get_id() == project_id for proj in proj_list]):
        return True
    else:
        return False


def sample_exists(api, sample):

    sample_list = api.get_samples(sample=sample)
    print [s for s in sample_list]
    if any([s.get_id() == sample.get_id() for s in sample_list]):
        return True
    else:
        return False
