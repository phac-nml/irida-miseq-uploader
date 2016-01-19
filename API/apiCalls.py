import ast
import json
import httplib
from urllib2 import urlopen, URLError
from urlparse import urljoin
from time import time
from copy import deepcopy
from os import path, system
from ConfigParser import RawConfigParser
import logging

from rauth import OAuth2Service
from requests.exceptions import HTTPError as request_HTTPError
from requests_toolbelt.multipart import encoder
from pubsub import pub
from appdirs import user_config_dir

from Model.Project import Project
from Model.Sample import Sample
from Exceptions.ProjectError import ProjectError
from Exceptions.SampleError import SampleError
from Exceptions.SequenceFileError import SequenceFileError
from Exceptions.SampleSheetError import SampleSheetError
from Validation.offlineValidation import validate_URL_form


# https://andrefsp.wordpress.com/2012/08/23/writing-a-class-decorator-in-python/
def method_decorator(fn):

    def decorator(*args, **kwargs):

        """
        Run the function (fn) and if any errors are raised then
        the publisher sends a messaage which calls
        handle_api_thread_error() in iridaUploaderMain.MainPanel
        """

        res = None
        try:
            res = fn(*args, **kwargs)
        except Exception, e:

            if fn.__name__ == "send_pair_sequence_files":

                if len(e.args) > 1:
                    err_msg, uploaded_samples_q = e.args
                    pub.sendMessage(
                        "handle_api_thread_error",
                        function_name=fn.__name__,
                        exception_error=e.__class__,
                        error_msg="".join(err_msg),
                        uploaded_samples_q=uploaded_samples_q)

                else:

                    pub.sendMessage(
                        "handle_api_thread_error",
                        function_name=fn.__name__,
                        exception_error=e.__class__,
                        error_msg=e.message)

            else:

                pub.sendMessage(
                    "handle_api_thread_error",
                    function_name=fn.__name__,
                    exception_error=e.__class__,
                    error_msg=e.message)

                raise

        return res

    return decorator


def class_decorator(*method_names):
    def class_rebuilder(cls):

        class NewClass(cls):

            def __getattribute__(self, attr_name):
                obj = super(NewClass, self).__getattribute__(attr_name)
                if hasattr(obj, '__call__') and attr_name in method_names:
                    return method_decorator(obj)
                return obj

        return NewClass
    return class_rebuilder


@class_decorator(
    "get_projects", "get_samples", "get_sequence_files",
    "send_project", "send_samples", "_send_pair_sequence_files"
    "get_pair_seq_runs", "create_seq_run",
    "_set_pair_seq_run_upload_status"
)
class ApiCalls(object):

    def __init__(self, client_id, client_secret,
                 base_URL, username, password, max_wait_time=20):
        """
        Create OAuth2Session and store it

        arguments:
            client_id -- client_id for creating access token.
            client_secret -- client_secret for creating access token.
            base_URL -- url of the IRIDA server
            username -- username for server
            password -- password for given username

        return ApiCalls object
        """

        self.client_id = client_id
        self.client_secret = client_secret
        self.base_URL = base_URL
        self.username = username
        self.password = password
        self.max_wait_time = max_wait_time

        self.conf_parser = RawConfigParser()
        self.config_file = path.join(user_config_dir("iridaUploader"),
                                     "config.conf")
        self.conf_parser.read(self.config_file)

        self.create_session()
        self.cached_projects = None
        self.cached_samples = {}

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
            self.session = oauth_service.get_session(access_token)

            if self.validate_URL_existence(self.base_URL, use_session=True) is\
                    False:
                raise Exception("Cannot create session. " +
                                "Verify your credentials are correct.")

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

        retVal = None

        if self.validate_URL_existence(targ_url, use_session=True):
            response = self.session.get(targ_url)

            if len(targ_dict) > 0:
                resources_list = response.json()["resource"]["resources"]
                try:
                    links_list = next(r["links"] for r in resources_list
                                      if r[targ_dict["key"]] ==
                                      targ_dict["value"])

                except KeyError:
                    raise KeyError(targ_dict["key"] + " not found." +
                                   " Available keys: " +
                                   ", ".join(resources_list[0].keys()))

                except StopIteration:
                    raise KeyError(targ_dict["value"] + " not found.")

            else:
                links_list = response.json()["resource"]["links"]
            try:
                retVal = next(link["href"] for link in links_list
                              if link["rel"] == target_key)

            except StopIteration:
                raise KeyError(target_key + " not found in links. " +
                               "Available links: " +
                               ", ".join(
                                [str(link["rel"]) for link in links_list]))

        else:
            raise request_HTTPError("Error: " +
                                    targ_url + " is not a valid URL")

        return retVal

    def get_projects(self):
        """
        API call to api/projects to get list of projects

        returns list containing projects. each project is Project object.
        """

        if self.cached_projects is None:

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
            project_id = sample["sampleProject"]
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
                raise ProjectError("The given project ID: " +
                                   project_id + " doesn't exist")

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
            raise SampleError("The given sample ID: " +
                              sample_id + " doesn't exist")

        result = response.json()["resource"]["resources"]

        return result

    def send_project(self, project):
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
                raise SampleError(("Error {status_code}: {err_msg}.\n" +
                                  "Sample data: {sample_data}").format(
                                  status_code=str(response.status_code),
                                  err_msg=response.text,
                                  sample_data=str(sample)))
        return json_res_list

    def get_file_size_list(self, samples_list):
        """
        calculate file size for the pair files in a sample

        arguments:
            samples_list -- list containing Sample object(s)

        returns list containing file sizes for each sample's pair files
        """

        file_size_list = []
        for sample in samples_list:

            bytes_read_size = sample.get_pair_files_size()
            file_size_list.append(bytes_read_size)
            sample.pair_files_byte_size = bytes_read_size

        return file_size_list

    def prune_samples_list(self, prev_uploaded_samples, samples_list):

        """
        Remove each sequence file from samples_list that is in
        prev_uploaded_samples

        no return value
        """

        for sample_id in prev_uploaded_samples:
            for sample in samples_list:
                if sample_id == sample.get_id():
                    samples_list.remove(sample)
                    break

    def send_pair_sequence_files(self, samples_list, callback=None,
                                 upload_id=1,
                                 prev_uploaded_samples=[],
                                 uploaded_samples_q=None):

        """
        send pair sequence files found in each sample in samples_list
        the pair files to be sent is in sample.get_pair_files()
        this function iterates through the samples in samples_list and send
        them to _send_pair_sequence_files() which actually makes the connection
        to the api in order to send the data

        arguments:
            samples_list -- list containing Sample object(s)
            callback -- optional callback argument for use with monitor
                        callback function accepts a
                        encoder.MultipartEncoderMonitor object as it's only
                        parameter

        returns a list containing dictionaries of the result of post request.
        """

        json_res_list = []

        if prev_uploaded_samples:
            self.prune_samples_list(prev_uploaded_samples, samples_list)

        file_size_list = self.get_file_size_list(samples_list)
        self.size_of_all_seq_files = sum(file_size_list)

        self.total_bytes_read = 0
        self.start_time = time()

        for sample in samples_list:

            json_res = self._send_pair_sequence_files(sample, callback,
                                                      upload_id,
                                                      uploaded_samples_q)
            json_res_list.append(json_res)

        if callback is not None:
            pub.sendMessage("pair_seq_files_upload_complete")
            completion_cmd = self.conf_parser.get("Settings", "completion_cmd")
            if len(completion_cmd) > 0:
                pub.sendMessage("display_completion_cmd_msg",
                                completion_cmd=completion_cmd)
                system(completion_cmd)

        return json_res_list

    def _send_pair_sequence_files(self, sample, callback, upload_id,
                                  uploaded_samples_q):

        """
        post request to send pair sequence files found in given sample argument
        raises error if either project ID or sample ID found in Sample object
        doesn't exist in irida

        arguments:
            sample -- Sample object
            callback -- optional callback argument for use with monitor
                        callback function accepts a
                        encoder.MultipartEncoderMonitor object as it's only
                        parameter

        returns result of post request.
        """

        json_res = {}

        try:
            project_id = sample.get_project_id()
            proj_URL = self.get_link(self.base_URL, "projects")
            samples_url = self.get_link(proj_URL, "project/samples",
                                        targ_dict={
                                            "key": "identifier",
                                            "value": project_id
                                        })
        except StopIteration:
            raise ProjectError("The given project ID: " +
                               project_id + " doesn't exist")

        try:
            sample_id = sample.get_id()
            seq_url = self.get_link(samples_url, "sample/sequenceFiles",
                                    targ_dict={
                                        "key": "sampleName",
                                        "value": sample_id
                                    })
        except StopIteration:
            raise SampleError("The given sample ID: " +
                              sample_id + " doesn't exist")

        miseqRunId_key = "miseqRunId"

        if sample.is_paired_end():
            logging.warn("sending paired-end file")
            url = self.get_link(seq_url, "sample/sequenceFiles/pairs")
            parameters1 = ("\"{key1}\": \"{value1}\"," +
                           "\"{key2}\": \"{value2}\"").format(
                            key1=miseqRunId_key, value1=str(upload_id),
                            key2="parameter1", value2="p1")
            parameters1 = "{" + parameters1 + "}"

            parameters2 = ("\"{key1}\": \"{value1}\", " +
                           "\"{key2}\": \"{value2}\"").format(
                            key1=miseqRunId_key, value1=str(upload_id),
                            key2="parameter2", value2="p2")
            parameters2 = "{" + parameters2 + "}"

            files = ({
                    "file1": (sample.get_pair_files()[0].replace("\\", "/"),
                              open(sample.get_pair_files()[0], "rb")),
                    "parameters1": ("", parameters1, "application/json"),
                    "file2": (sample.get_pair_files()[1].replace("\\", "/"),
                              open(sample.get_pair_files()[1], "rb")),
                    "parameters2": ("", parameters2, "application/json")
            })

        else:
            logging.warn("sending single-end file")
            url = seq_url
            parameters1 = ("\"{key1}\": \"{value1}\"," +
                           "\"{key2}\": \"{value2}\"").format(
                            key1=miseqRunId_key, value1=str(upload_id),
                            key2="parameter1", value2="p1")
            parameters1 = "{" + parameters1 + "}"

            files = ({
                    "file": (sample.get_pair_files()[0].replace("\\", "/"),
                              open(sample.get_pair_files()[0], "rb")),
                    "parameters": ("", parameters1, "application/json")
            })

        e = encoder.MultipartEncoder(fields=files)

        monitor = encoder.MultipartEncoderMonitor(e, callback)

        monitor.files = deepcopy(sample.get_pair_files())
        monitor.total_bytes_read = self.total_bytes_read
        monitor.size_of_all_seq_files = self.size_of_all_seq_files

        monitor.ov_upload_pct = 0.0
        monitor.cf_upload_pct = 0.0
        monitor.prev_cf_pct = 0.0
        monitor.prev_ov_pct = 0.0
        monitor.prev_bytes = 0

        monitor.start_time = self.start_time

        headers = {"Content-Type": monitor.content_type}

        response = self.session.post(url, data=monitor, headers=headers)
        self.total_bytes_read = monitor.total_bytes_read

        # response.status_code = 500

        if response.status_code == httplib.CREATED:
            json_res = json.loads(response.text)

            if uploaded_samples_q is not None:
                uploaded_samples_q.put(sample.get_id())

        else:

            err_msg = ("Error {status_code}: {err_msg}\n" +
                       "Upload data: {ud}").format(
                       status_code=str(response.status_code),
                       err_msg=response.reason,
                       ud=str(files))

            raise SequenceFileError(err_msg, uploaded_samples_q)

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

    def get_pair_seq_runs(self):

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

    def set_pair_seq_run_complete(self, identifier):

        """
        Update a sequencing run's upload status to "COMPLETE"

        arguments:
            identifier -- the id of the sequencing run to be updated

        returns result of patch request
        """

        status = "COMPLETE"
        json_res = self._set_pair_seq_run_upload_status(identifier, status)

        return json_res

    def set_pair_seq_run_uploading(self, identifier):

        """
        Update a sequencing run's upload status to "UPLOADING"

        arguments:
            identifier -- the id of the sequencing run to be updated

        returns result of patch request
        """

        status = "UPLOADING"
        json_res = self._set_pair_seq_run_upload_status(identifier, status)

        return json_res

    def set_pair_seq_run_error(self, identifier):

        """
        Update a sequencing run's upload status to "ERROR"

        arguments:
            identifier -- the id of the sequencing run to be updated

        returns result of patch request
        """

        status = "ERROR"
        json_res = self._set_pair_seq_run_upload_status(identifier, status)

        return json_res

    def _set_pair_seq_run_upload_status(self, identifier, status):

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
