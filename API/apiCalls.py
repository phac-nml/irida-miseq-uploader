import ast
import json
import httplib
import itertools
from urllib2 import urlopen, URLError
from urlparse import urljoin
from time import time
from copy import deepcopy
from os import path
import logging
import threading

from rauth import OAuth2Service
from requests.exceptions import HTTPError as request_HTTPError

from Model.Project import Project
from Model.Sample import Sample
from Exceptions.ProjectError import ProjectError
from Exceptions.SampleError import SampleError
from Exceptions.SequenceFileError import SequenceFileError
from Exceptions.SampleSheetError import SampleSheetError
from Validation.offlineValidation import validate_URL_form
from API.pubsub import send_message


class ApiCalls(object):

    _instance = None

    def __new__(cls, client_id, client_secret, base_URL, username, password, max_wait_time=20):
        """
            Overriding __new__ to implement a singleton
            This is done instead of a decorator so that mocking still works for class.
            If the instance has not been created yet, or the passed in arguments are different, create a new instance,
                and drop the old (if existing) instance
            If the instance already exists and is valid, return the instance
        """

        if not ApiCalls._instance or ApiCalls._instance.parameters_are_different(
                client_id, client_secret, base_URL,username, password, max_wait_time):

            # Create a new instance of the API
            ApiCalls._instance = object.__new__(cls)

            # initialize API instance variables
            ApiCalls._instance.client_id = client_id
            ApiCalls._instance.client_secret = client_secret
            ApiCalls._instance.base_URL = base_URL
            ApiCalls._instance.username = username
            ApiCalls._instance.password = password
            ApiCalls._instance.max_wait_time = max_wait_time

            # initialize API object
            ApiCalls._instance._session_lock = threading.Lock()
            ApiCalls._instance._session_set_externally = False
            ApiCalls._instance.create_session()
            ApiCalls._instance.cached_projects = None
            ApiCalls._instance.cached_samples = {}

        return ApiCalls._instance

    def parameters_are_different(self, client_id, client_secret, base_URL, username, password, max_wait_time):
        """
        Compare the current instance variables with a new set of variables
        """

        return (self.client_id != client_id or
                self.client_secret != client_secret or
                self.base_URL != base_URL or
                self.username != username or
                self.password != password or
                self.max_wait_time != max_wait_time)

    @property
    def session(self):
        if self._session_set_externally:
            return self._session

        try:
            self._session_lock.acquire()
            response = self._session.options(self.base_URL)
            if response.status_code != httplib.OK:
                raise Exception
            else:
                logging.debug("Existing session still works, going to reuse it.")
        except:
            logging.debug("Token is probably expired, going to get a new session.")
            oauth_service = self.get_oauth_service()
            access_token = self.get_access_token(oauth_service)
            self._session = oauth_service.get_session(access_token)
        finally:
            self._session_lock.release()

        return self._session

    @session.setter
    def session(self, session):
        self._session = session
        self._session_set_externally = True

    def create_session(self):
        """
        create session to be re-used until expiry for get and post calls

        returns session (OAuth2Session object)
        """

        if self.base_URL[-1:] != "/":
            self.base_URL = self.base_URL + "/"

        if validate_URL_form(self.base_URL):
            oauth_service = self.get_oauth_service()
            access_token = self.get_access_token(oauth_service)
            self._session = oauth_service.get_session(access_token)

            if self.validate_URL_existence(self.base_URL, use_session=True) is False:
                raise Exception("Cannot create session. Verify your credentials are correct.")
        else:
            raise URLError(self.base_URL + " is not a valid URL")

    def get_oauth_service(self):
        """
        get oauth service to be used to get access token

        returns oauthService
        """

        access_token_url = urljoin(self.base_URL, "oauth/token")
        oauth_serv = OAuth2Service(
            client_id=self.client_id,
            client_secret=self.client_secret,
            name="irida",
            access_token_url=access_token_url,
            base_url=self.base_URL
        )

        return oauth_serv

    def get_access_token(self, oauth_service):
        """
        get access token to be used to get session from oauth_service

        arguments:
            oauth_service -- O2AuthService from get_oauth_service

        returns access token
        """

        params = {
            "data": {
                "grant_type": "password",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "username": self.username,
                "password": self.password
            }
        }
        access_token = oauth_service.get_access_token(
            decoder=self.decoder, **params)
        return access_token

    def decoder(self, return_dict):
        """
        safely parse given dictionary

        arguments:
            return_dict -- access token dictionary

        returns evaluated dictionary
        """

        irida_dict = ast.literal_eval(return_dict)
        return irida_dict

    def validate_URL_existence(self, url, use_session=False):
        """
        tries to validate existence of given url by trying to open it.
        true if HTTP OK, false if HTTP NOT FOUND otherwise
            raises error containing error code and message

        arguments:
            url -- the url link to open and validate
            use_session -- if True then this uses self.session.get(url) instead
            of urlopen(url) to get response

        returns
            true if http response OK 200
            false if http response NOT FOUND 404
        """

        if use_session:
            response = self.session.get(url)

            if response.status_code == httplib.OK:
                return True
            elif response.status_code == httplib.NOT_FOUND:
                return False
            else:
                raise Exception(
                    str(response.status_code) + " " + response.reason)

        else:
            response = urlopen(url, timeout=self.max_wait_time)

            if response.code == httplib.OK:
                return True
            elif response.code == httplib.NOT_FOUND:
                return False
            else:
                raise Exception(str(response.code) + " " + response.msg)

    def get_link(self, targ_url, target_key, targ_dict=""):
        """
        makes a call to targ_url(api) expecting a json response
        tries to retrieve target_key from response to find link to resource
        raises exceptions if target_key not found or targ_url is invalid

        arguments:
            targ_url -- URL to retrieve link from
            target_key -- name of link (e.g projects or project/samples)
            targ_dict -- optional dict containing key and value to search
                in targets.
            (e.g {key="identifier",value="100"} to retrieve where
                identifier=100)

        returns link if it exists
        """

        if self.validate_URL_existence(targ_url, use_session=True):
            response = self.session.get(targ_url)

            if len(targ_dict) > 0:
                resources_list = response.json()["resource"]["resources"]
                try:
                    links_list = next(r["links"] for r in resources_list
                                      if r[targ_dict["key"]].lower() ==
                                      targ_dict["value"].lower())

                except KeyError:
                    raise KeyError(targ_dict["key"] + " not found." +
                                   " Available keys: " +
                                   ", ".join(resources_list[0].keys()))

                except StopIteration:
                    raise KeyError(targ_dict["value"] + " not found.")

            else:
                links_list = response.json()["resource"]["links"]
            try:
                ret_val = next(link["href"] for link in links_list
                              if link["rel"] == target_key)

            except StopIteration:
                raise KeyError(target_key + " not found in links. " +
                               "Available links: " +
                               ", ".join(
                                [str(link["rel"]) for link in links_list]))

        else:
            raise request_HTTPError("Error: " +
                                    targ_url + " is not a valid URL")

        return ret_val

    def get_projects(self):
        """
        API call to api/projects to get list of projects

        returns list containing projects. each project is Project object.
        """

        if self.cached_projects is None:
            logging.info("Loading projects from server.")
            url = self.get_link(self.base_URL, "projects")
            response = self.session.get(url)

            result = response.json()["resource"]["resources"]
            try:
                project_list = [
                    Project(
                        projDict["name"],
                        projDict["projectDescription"],
                        projDict["identifier"]
                    )
                    for projDict in result
                ]

            except KeyError, e:
                e.args = map(str, e.args)
                msg_arg = " ".join(e.args)
                raise KeyError(msg_arg + " not found." + " Available keys: " +
                               ", ".join(result[0].keys()))
            self.cached_projects = project_list
        else:
            logging.info("Loading projects from cache.")

        return self.cached_projects

    def get_samples(self, project=None, sample=None):
        """
        API call to api/projects/project_id/samples

        arguments:
            project -- a Project object used to get project_id

        returns list of samples for the given project.
            each sample is a Sample object.
        """

        if sample is not None:
            project_id = sample.get_project_id()
        elif project is not None:
            project_id = project.get_id()
        else:
            raise Exception("Missing project or sample object.")

        if project_id not in self.cached_samples:
            try:
                proj_URL = self.get_link(self.base_URL, "projects")
                url = self.get_link(proj_URL, "project/samples",
                                    targ_dict={
                                        "key": "identifier",
                                        "value": project_id
                                    })

            except StopIteration:
                raise ProjectError("The given project ID: " + project_id + " doesn't exist")

            response = self.session.get(url)
            result = response.json()["resource"]["resources"]
            self.cached_samples[project_id] = [Sample(sample_dict) for sample_dict in result]

        return self.cached_samples[project_id]

    def get_sequence_files(self, sample):
        """
        API call to api/projects/project_id/sample_id/sequenceFiles

        arguments:

            sample -- a Sample object used to get sample_id

        returns list of sequencefile dictionary for given sample_id
        """

        project_id = sample.get_project_id()
        sample_id = sample.get_id()

        try:
            proj_URL = self.get_link(self.base_URL, "projects")
            sample_URL = self.get_link(proj_URL, "project/samples",
                                       targ_dict={
                                           "key": "identifier",
                                           "value": project_id
                                       })

        except StopIteration:
            raise ProjectError("The given project ID: " +
                               project_id + " doesn't exist")

        try:
            url = self.get_link(sample_URL, "sample/sequenceFiles",
                                targ_dict={
                                    "key": "sampleName",
                                    "value": sample_id
                                })

            response = self.session.get(url)

        except StopIteration:
            raise SampleError("The given sample ID: {} doesn't exist".format(sample_id), [])

        result = response.json()["resource"]["resources"]

        return result

    def send_project(self, project, clear_cache=True):
        """
        post request to send a project to IRIDA via API
        the project being sent requires a name that is at least
            5 characters long

        arguments:
            project -- a Project object to be sent.

        returns a dictionary containing the result of post request.
        when post is successful the dictionary it returns will contain the same
            name and projectDescription that was originally sent as well as
            additional keys like createdDate and identifier.
        when post fails then an error will be raised so return statement is
            not even reached.
        """
        if clear_cache:
            self.cached_projects = None

        json_res = {}
        if len(project.get_name()) >= 5:
            url = self.get_link(self.base_URL, "projects")
            json_obj = json.dumps(project.get_dict())
            headers = {
                "headers": {
                    "Content-Type": "application/json"
                }
            }

            response = self.session.post(url, json_obj, **headers)
            if response.status_code == httplib.CREATED:  # 201
                json_res = json.loads(response.text)
            else:
                raise ProjectError("Error: " +
                                   str(response.status_code) + " " +
                                   response.text)

        else:
            raise ProjectError("Invalid project name: " +
                               project.get_name() +
                               ". A project requires a name that must be " +
                               "5 or more characters.")

        return json_res

    def send_samples(self, samples_list):
        """
        post request to send sample(s) to the given project
        the project that the sample will be sent to is in its dictionary's
        "sampleProject" key

        arguments:
            samples_list -- list containing Sample object(s) to send

        returns a list containing dictionaries of the result of post request.
        """

        self.cached_samples = {} # reset the cache, we're updating stuff
        self.cached_projects = None
        json_res_list = []

        for sample in samples_list:

            try:
                project_id = sample.get_project_id()
                proj_URL = self.get_link(self.base_URL, "projects")
                url = self.get_link(proj_URL, "project/samples",
                                    targ_dict={
                                        "key": "identifier",
                                        "value": project_id
                                    })

            except StopIteration:
                raise ProjectError("The given project ID: " +
                                   project_id + " doesn't exist")

            headers = {
                "headers": {
                    "Content-Type": "application/json"
                }
            }

            json_obj = json.dumps(sample, cls=Sample.JsonEncoder)
            response = self.session.post(url, json_obj, **headers)

            if response.status_code == httplib.CREATED:  # 201
                json_res = json.loads(response.text)
                json_res_list.append(json_res)
            else:
                logging.error("Didn't create sample on server, response code is [{}] and error message is [{}]".format(response.status_code, response.text))
                e = SampleError("Error {status_code}: {err_msg}.\nSample data: {sample_data}".format(status_code=str(response.status_code), err_msg=response.text, sample_data=str(sample)), ["IRIDA rejected the sample."])
                send_message(sample.upload_failed_topic, exception = e)
                raise e

        return json_res_list

    def get_file_size_list(self, samples_list):
        """
        calculate file size for the files in a sample

        arguments:
            samples_list -- list containing Sample object(s)

        returns list containing file sizes for each sample's files
        """

        file_size_list = []
        for sample in samples_list:

            bytes_read_size = sample.get_files_size()
            file_size_list.append(bytes_read_size)
            sample.pair_files_byte_size = bytes_read_size

        return file_size_list

    def send_sequence_files(self, samples_list, upload_id=1):

        """
        send sequence files found in each sample in samples_list
        the files to be sent is in sample.get_files()
        this function iterates through the samples in samples_list and send
        them to _send_sequence_files() which actually makes the connection
        to the api in order to send the data

        arguments:
            samples_list -- list containing Sample object(s)
            upload_id -- the run to send the files to

        returns a list containing dictionaries of the result of post request.
        """

        json_res_list = []

        file_size_list = self.get_file_size_list(samples_list)
        self.size_of_all_seq_files = sum(file_size_list)

        self.total_bytes_read = 0
        self.start_time = time()

        for sample in samples_list:
            try:
                json_res = self._send_sequence_files(sample, upload_id)
                json_res_list.append(json_res)
            except Exception, e:
                logging.error("The upload failed for unexpected reasons, informing the UI.")
                send_message(sample.upload_failed_topic, exception = e)
                raise
        return json_res_list

    def _kill_connections(self):
        """Terminate any currently running uploads.

        This method simply sets a flag to instruct any in-progress generators called
        by `_send_sequence_files` below to stop generating data and raise an exception
        that will set the run to an error state on the server.
        """

        self._stop_upload = True
        self.session.close()

    def _send_sequence_files(self, sample, upload_id):

        """
        post request to send sequence files found in given sample argument
        raises error if either project ID or sample ID found in Sample object
        doesn't exist in irida

        arguments:
            sample -- Sample object
            upload_id -- the run to upload the files to

        returns result of post request.
        """

        json_res = {}
        self._stop_upload = False

        try:
            project_id = sample.get_project_id()
            proj_URL = self.get_link(self.base_URL, "projects")
            samples_url = self.get_link(proj_URL, "project/samples",
                                        targ_dict={
                                            "key": "identifier",
                                            "value": project_id
                                        })
        except StopIteration:
            raise ProjectError("The given project ID: " + project_id + " doesn't exist")

        try:
            sample_id = sample.get_id()
            seq_url = self.get_link(samples_url, "sample/sequenceFiles",
                                    targ_dict={
                                        "key": "sampleName",
                                        "value": sample_id
                                    })
        except StopIteration:
            raise SampleError("The given sample ID: {} doesn't exist".format(sample_id),
                ["No sample with name [{}] exists in project [{}]".format(sample_id, project_id)])

        boundary = "B0undary"
        read_size = 32768

        def _send_file(filename, parameter_name, bytes_read=0):
            """This function is a generator that yields a multipart form-data
            entry for the specified file. This function will yield `read_size`
            bytes of the specified file name at a time as the generator is called.
            This function will also terminate generating data when the field
            `self._stop_upload` is set.

            Args:
                filename: the file to read and yield in `read_size` chunks to
                          the server.
                parameter_name: the form field name to send to the server.
                bytes_read: used for sending messages to the UI layer indicating
                            the total number of bytes sent when sending the sample
                            to the server.
            """

            # Send the boundary header section for the file
            logging.info("Sending the boundary header section for {}".format(filename))
            yield ("\r\n--{boundary}\r\n"
            "Content-Disposition: form-data; name=\"{parameter_name}\"; filename=\"{filename}\"\r\n"
            "\r\n").format(boundary=boundary, parameter_name=parameter_name, filename=filename.replace("\\", "/"))

            # Send the contents of the file, read_size bytes at a time until
            # we've either read the entire file, or we've been instructed to
            # stop the upload by the UI
            logging.info("Starting to send the file {}".format(filename))
            with open(filename, "rb", read_size) as fastq_file:
                data = fastq_file.read(read_size)
                while data and not self._stop_upload:
                    bytes_read += len(data)
                    send_message(sample.upload_progress_topic, progress=bytes_read)
                    yield data
                    data = fastq_file.read(read_size)
                logging.info("Finished sending file {}".format(filename))
                if self._stop_upload:
                    logging.info("Halting upload on user request.")

        def _send_parameters(parameter_name, parameters):
            """This function is a generator that yields a multipart form-data
            entry with additional file metadata.

            Args:
                parameter_name: the form field name to use to send to the server.
                parameters: a JSON encoded object with the metadata for the file.
            """

            logging.info("Going to send parameters for {}".format(parameter_name))
            yield ("\r\n--{boundary}\r\n"
            "Content-Disposition: form-data; name=\"{parameter_name}\"\r\n"
            "Content-Type: application/json\r\n\r\n"
            "{parameters}\r\n").format(boundary=boundary, parameter_name=parameter_name, parameters=parameters)

        def _finish_request():
            """This function is a generator that yields the terminal boundary
            entry for a multipart form-data upload."""

            yield "--{boundary}--".format(boundary=boundary)

        def _sample_upload_generator(sample):
            """This function accepts the sample and composes a series of generators
            that are used to send the file contents and metadata for the sample.

            Args:
                sample: the sample to send to the server
            """

            bytes_read = 0

            file_metadata = sample.get_sample_metadata()
            file_metadata["miseqRunId"] = str(upload_id)
            file_metadata_json = json.dumps(file_metadata)

            if sample.is_paired_end():
                # Compose a collection of generators to send both files of a paired-end
                # file set and the corresponding metadata
                return itertools.chain(
                    _send_file(filename=sample.get_files()[0], parameter_name="file1"),
                    _send_file(filename=sample.get_files()[1], parameter_name="file2", bytes_read=path.getsize(sample.get_files()[0])),
                    _send_parameters(parameter_name="parameters1", parameters=file_metadata_json),
                    _send_parameters(parameter_name="parameters2", parameters=file_metadata_json),
                    _finish_request())
            else:
                # Compose a generator to send the single file from a single-end
                # file set and the corresponding metadata.
                return itertools.chain(
                    _send_file(filename=sample.get_files()[0], parameter_name="file"),
                    _send_parameters(parameter_name="parameters", parameters=file_metadata_json),
                    _finish_request())

        if sample.is_paired_end():
            logging.info("sending paired-end file")
            url = self.get_link(seq_url, "sample/sequenceFiles/pairs")
        else:
            logging.info("sending single-end file")
            url = seq_url

        send_message(sample.upload_started_topic)

        logging.info("Sending files to [{}]".format(url))
        response = self.session.post(url, data=_sample_upload_generator(sample),
                                     headers={"Content-Type": "multipart/form-data; boundary={}".format(boundary)})

        if self._stop_upload:
            logging.info("Upload was halted on user request, raising exception so that server upload status is set to error state.")
            raise SequenceFileError("Upload halted on user request.", [])

        if response.status_code == httplib.CREATED:
            json_res = json.loads(response.text)
            logging.info("Finished uploading sequence files for sample [{}]".format(sample.get_id()))
            send_message(sample.upload_completed_topic, sample=sample)
        else:
            e = SequenceFileError("Error {status_code}: {err_msg}\n".format(
                       status_code=str(response.status_code),
                       err_msg=response.reason))
            logging.info("Got an error when uploading [{}]: [{}]".format(sample.get_id(), err_msg))
            logging.info(response.text)
            send_message(sample.upload_failed_topic, exception=e)
            raise e

        return json_res

    def create_seq_run(self, metadata_dict):

        """
        Create a sequencing run.

        the contents of metadata_dict are changed inside this method (THIS IS TERRIBLE)

        uploadStatus "UPLOADING"

        There are some parsed metadata keys from the SampleSheet.csv that are
        currently not accepted/used by the API so they are discarded.
        Everything not in the acceptable_properties list below is discarded.

        arguments:
            metadata_dict -- SequencingRun's metadata parsed from
                             a Samplesheet.csv file by
                             miseqParser.parse_metadata()

        returns result of post request.
        """

        json_res = {}

        seq_run_url = self.get_link(self.base_URL, "sequencingRuns")

        url = self.get_link(seq_run_url, "sequencingRun/miseq")

        headers = {
            "headers": {
                "Content-Type": "application/json"
            }
        }

        acceptable_properties = [
            "layoutType", "chemistry", "projectName",
            "experimentName", "application", "uploadStatus",
            "investigatorName", "createdDate", "assay", "description",
            "workflow", "readLengths"]

        metadata_dict["uploadStatus"] = "UPLOADING"

        for key in metadata_dict.keys():
            if key not in acceptable_properties:
                del metadata_dict[key]

        json_obj = json.dumps(metadata_dict)
        response = self.session.post(url, json_obj, **headers)
        if response.status_code == httplib.CREATED:  # 201
            json_res = json.loads(response.text)
        else:
            raise SampleSheetError("Error: " +
                                   str(response.status_code) + " " +
                                   response.reason)
        return json_res

    def get_seq_runs(self):

        """
        Get list of pair files SequencingRuns
        /api/sequencingRuns returns all SequencingRuns so this method
        checks each SequencingRuns's layoutType to be equal to "PAIRED_END"
        if it is add it to the list

        return list of paired files SequencingRuns
        """

        url = self.get_link(self.base_URL, "sequencingRuns")
        response = self.session.get(url)

        json_res_list = response.json()["resource"]["resources"]

        pair_seq_run_list = [json_res
                             for json_res in json_res_list
                             if json_res["layoutType"] == "PAIRED_END"]

        return pair_seq_run_list

    def set_seq_run_complete(self, identifier):

        """
        Update a sequencing run's upload status to "COMPLETE"

        arguments:
            identifier -- the id of the sequencing run to be updated

        returns result of patch request
        """

        status = "COMPLETE"
        json_res = self._set_seq_run_upload_status(identifier, status)

        return json_res

    def set_seq_run_uploading(self, identifier):

        """
        Update a sequencing run's upload status to "UPLOADING"

        arguments:
            identifier -- the id of the sequencing run to be updated

        returns result of patch request
        """

        status = "UPLOADING"
        json_res = self._set_seq_run_upload_status(identifier, status)

        return json_res

    def set_seq_run_error(self, identifier):

        """
        Update a sequencing run's upload status to "ERROR".

        arguments:
            identifier -- the id of the sequencing run to be updated

        returns result of patch request
        """

        status = "ERROR"
        json_res = self._set_seq_run_upload_status(identifier, status)

        return json_res

    def _set_seq_run_upload_status(self, identifier, status):

        """
        Update a sequencing run's upload status to the given status argument

        arguments:
            identifier -- the id of the sequencing run to be updated
            status     -- string that the sequencing run will be updated
                          with

        returns result of patch request
        """

        json_res = {}

        seq_run_url = self.get_link(self.base_URL, "sequencingRuns")

        url = self.get_link(seq_run_url, "self",
                            targ_dict={
                                "key": "identifier",
                                "value": identifier
                            })
        headers = {
            "headers": {
                "Content-Type": "application/json"
            }
        }

        update_dict = {"uploadStatus": status}
        json_obj = json.dumps(update_dict)

        response = self.session.patch(url, json_obj, **headers)

        if response.status_code == httplib.OK:  # 200
            json_res = json.loads(response.text)
        else:
            raise SampleSheetError("Error: " +
                                   str(response.status_code) + " " +
                                   response.reason)

        return json_res
