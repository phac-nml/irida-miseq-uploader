import ast
import json
import httplib
from os import path
from urllib2 import Request, urlopen, URLError, HTTPError
from urlparse import urljoin

from rauth import OAuth2Service, OAuth2Session
from requests import Request
from requests.exceptions import HTTPError as request_HTTPError
from requests_toolbelt.multipart import encoder

from Model.SequenceFile import SequenceFile
from Model.Project import Project
from Model.Sample import Sample
from Model.ValidationResult import ValidationResult
from Exceptions.ProjectError import ProjectError
from Exceptions.SampleError import SampleError
from Exceptions.SequenceFileError import SequenceFileError
from Validation.offlineValidation import validate_URL_form


class ApiCalls:

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

        self.create_session()

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

        return project_list

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
        sample_list = [Sample(sample_dict) for sample_dict in result]

        return sample_list

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
                                    "key": "sequencerSampleId",
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

        json_res = None
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

    def send_pair_sequence_files(self, samples_list, gui_main=None):
        """
        send pair sequence files found in each sample in samples_list
        the pair files to be sent is in sample.get_pair_files()

        arguments:
            samples_list -- list containing Sample object(s)

        returns a list containing dictionaries of the result of post request.
        """
        def callback(monitor):

            monitor.upload_pct = ((monitor.bytes_read * 1.0) /
                                  (monitor.len * 1.0))
            monitor.upload_pct = round(monitor.upload_pct, 2)
            if monitor.prev_pct != monitor.upload_pct:
                print "{pct}%".format(pct=monitor.upload_pct)
                gui_main.progress_bar.SetValue(monitor.upload_pct * 100)
                gui_main.progress_label.SetLabel(str(monitor.upload_pct*100) +
                                                 "%")
                gui_main.Refresh()

            monitor.prev_pct = monitor.upload_pct

        json_res_list = []

        for sample in samples_list:

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
                                            "key": "sequencerSampleId",
                                            "value": sample_id
                                        })
            except StopIteration:
                raise SampleError("The given sample ID: " +
                                  sample_id + " doesn't exist")

            url = self.get_link(seq_url, "sample/sequenceFiles/pairs")

            files = ({
                    "file1": (sample.get_pair_files()[0],
                              open(sample.get_pair_files()[0], "rb")),
                    "parameters1": ("", "{\"parameters1\": \"p1\"}",
                                    "application/json"),
                    "file2": (sample.get_pair_files()[0],
                              open(sample.get_pair_files()[1], "rb")),
                    "parameters2": ("", "{\"parameters2\": \"p2\"}",
                                    "application/json")
            })

            e = encoder.MultipartEncoder(
                fields=files)
            monitor = encoder.MultipartEncoderMonitor(e, callback)
            headers = {"Content-Type": monitor.content_type}
            monitor.total_file_size = path.getsize(
                sample.get_pair_files()[0]) + path.getsize(
                sample.get_pair_files()[1])
            monitor.upload_pct = 0.0
            monitor.prev_pct = 0.0
            # https://github.com/kennethreitz/requests/issues/1495
            # content-type for parameters: ('filename', 'data', 'Content-Type)

            response = self.session.post(url, data=monitor, headers=headers)
            # print "Headers:", response.request.headers
            # print "Body:", response.request.body
            if response.status_code == httplib.CREATED:
                json_res = json.loads(response.text)
                json_res_list.append(json_res)
            else:
                raise SequenceFileError(("Error {status_code}: {err_msg}.\n" +
                                         "Upload data: {ud}").format(
                                         status_code=str(response.status_code),
                                         err_msg=response.text,
                                         ud=str(files)))

        return json_res_list
