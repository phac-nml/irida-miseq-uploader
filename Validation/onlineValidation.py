from API.pubsub import send_message
from requests import ConnectionError

def project_exists(api, project_id, message_id=None):
    try:
        proj_list = api.get_projects()
        project = next(proj for proj in proj_list if proj.get_id() == project_id)
        if message_id:
            send_message(message_id, project=project)
        return True
    except ConnectionError:
        if message_id:
            send_message(message_id, project=None)
    except StopIteration:
        if message_id:
            send_message(message_id, project=None)
        return False

def sample_exists(api, sample):

    sample_list = api.get_samples(sample=sample)

    if any([s.get_id().lower() == sample.get_id().lower() for s in sample_list]):
        return True
    else:
        return False
