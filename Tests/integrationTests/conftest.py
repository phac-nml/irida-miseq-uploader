import logging
import pytest

from API.apiCalls import ApiCalls
from apiCalls_integration_data_setup import SetupIridaData

base_URL = "http://localhost:8080/api"
username = "admin"
password = "Password1!"
client_id = ""
client_secret = ""

@pytest.fixture(scope="session")
def api(request):
    logging.warn("Starting IRIDA for integration tests.")
    branch = request.config.getoption("--irida-version")
    setup = start_setup(branch)
    request.addfinalizer(setup.stop_irida)
    return ApiCalls(
        client_id=client_id,
        client_secret=client_secret,
        base_URL=base_URL,
        username=username,
        password=password
    )

def irida_setup(setup):

    setup.install_irida()
    setup.reset_irida_db()
    setup.run_irida()


def data_setup(setup):

    irida_setup(setup)

    setup.start_driver()
    setup.login()
    setup.set_new_admin_pw()
    setup.create_client()

    irida_secret = setup.get_irida_secret()
    setup.close_driver()

    return(setup.IRIDA_AUTH_CODE_ID, irida_secret, setup.IRIDA_PASSWORD)


def start_setup(branch):

    global base_URL
    global username
    global password
    global client_id
    global client_secret

    setup = SetupIridaData(
        base_URL[:base_URL.index("/api")], username, password, branch)
    client_id, client_secret, password = data_setup(setup)

    return setup
