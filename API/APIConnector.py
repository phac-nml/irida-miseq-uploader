import logging
import threading

from os import path
from API.pubsub import send_message
from API import ApiCalls
from API.config import read_config_option
from requests.exceptions import ConnectionError
from urllib2 import URLError

class APIConnectorTopics(object):
    connection_error_topic = "APIConnector.connection_error_topic"
    connection_error_url_topic = connection_error_topic + ".url"
    connection_error_credentials_topic = connection_error_topic + ".credentials"
    connection_error_user_credentials_topic = connection_error_credentials_topic + ".user"
    connection_error_client_id_topic = connection_error_credentials_topic + ".client_id"
    connection_error_client_secret_topic = connection_error_credentials_topic + ".client_secret"
    connection_success_topic = "APIConnector.connection_success_topic"
    connection_success_valid_url = "APIConnector.connection_success_valid_url"
    connection_success_valid_client_id = "APIConnector.connection_success_valid_client_id"
    connection_success_valid_client_secret = "APIConnector.connection_success_valid_client_secret"

lock = threading.Lock()

def connect_to_irida():
    """Connect to IRIDA for online validation.

    Returns:
        A configured instance of API.apiCalls.
    """
    client_id = read_config_option("client_id")
    client_secret = read_config_option("client_secret")
    baseURL = read_config_option("baseURL")
    username = read_config_option("username")
    password = read_config_option("password")

    try:
        # Several threads might be attempting to connect at the same time, so lock
        # the connection step, but **do not** block (acquire(False) means do not block)
        # and just return if someone else is already trying to connect.
        if lock.acquire(False):
            logging.info("About to try connecting to IRIDA.")
            api = ApiCalls(client_id, client_secret, baseURL, username, password)
            send_message(APIConnectorTopics.connection_success_topic, api=api)
            return api
        else:
            logging.info("Someone else is already trying to connect to IRIDA.")
    except ConnectionError as e:
        logging.info("Got a connection error when trying to connect to IRIDA.", exc_info=True)
        send_message(APIConnectorTopics.connection_error_url_topic, error_message=(
            "We couldn't connect to IRIDA at {}. The server might be down. Make "
            "sure that the connection address is correct (you can change the "
            "address by clicking on the 'Open Settings' button below) and try"
            " again, try again later, or contact an administrator."
            ).format(baseURL))
        raise
    except (SyntaxError, ValueError) as e:
        logging.info("Connected, but the response was garbled.", exc_info=True)
        send_message(APIConnectorTopics.connection_error_url_topic, error_message=(
            "We couldn't connect to IRIDA at {}. The server is up, but I "
            "didn't understand the response. Make sure that the connection "
            "address is correct (you can change the address by clicking on "
            "the 'Open Settings' button below) and try again, try again"
            " later, or contact an administrator."
            ).format(baseURL))
        raise
    except KeyError as e:
        logging.info("Connected, but the OAuth credentials are wrong.", exc_info=True)

        # this is credentials related, but let's try to figure out why the server
        # is telling us that we can't log in.
        message = str(e.message)

        if "Bad credentials" in message:
            topic = APIConnectorTopics.connection_error_user_credentials_topic
            # if we're getting bad credentials, then that means the API is allowing
            # us to try authenticate with a username and password, so our client id
            # and secret are both correct:
            send_message(APIConnectorTopics.connection_success_valid_client_secret)
        elif "clientId does not exist" in message:
            topic = APIConnectorTopics.connection_error_client_id_topic
        elif "Bad client credentials" in message:
            topic = APIConnectorTopics.connection_error_client_secret_topic
            # if we're getting a bad client secret message, that means that the
            # client ID is valid.
            send_message(APIConnectorTopics.connection_success_valid_client_id)
        else:
            topic = APIConnectorTopics.connection_error_credentials_topic

        send_message(topic, error_message=(
            "We couldn't connect to IRIDA at {}. The server is up, but it's "
            "reporting that your credentials are wrong. Click on the 'Open Settings'"
            " button below and check your credentials, then try again. If the "
            "connection still doesn't work, contact an administrator."
            ).format(baseURL))

        # in spite of it all, this means that we're probably actually trying to connect
        # to a real IRIDA server, so let the settings dialog know that it can render
        # a success icon beside the URL
        send_message(APIConnectorTopics.connection_success_valid_url)
        raise
    except URLError as e:
        logging.info("Couldn't connect to IRIDA because the URL is invalid.", exc_info=True)
        send_message(APIConnectorTopics.connection_error_url_topic, error_message=(
            "We couldn't connect to IRIDA at {} because it isn't a valid URL. "
            "Click on the 'Open Settings' button below to enter a new URL and "
            "try again."
        ).format(baseURL))
        raise
    except:
        logging.info("Some other kind of error happened.", exc_info=True)
        send_message(APIConnectorTopics.connection_error_topic,  error_message=(
            "We couldn't connect to IRIDA at {} for an unknown reason. Click "
            "on the 'Open Settings' button below to check the URL and your "
            "credentials, then try again. If the connection still doesn't "
            "work, contact an administrator."
        ).format(baseURL))
        raise
    finally:
        try:
            lock.release()
        except:
            pass
