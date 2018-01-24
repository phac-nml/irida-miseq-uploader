import unittest
import json
import httplib
from urllib2 import URLError

from mock import patch, MagicMock
from requests.exceptions import HTTPError as request_HTTPError
from Model.SequenceFile import SequenceFile
from Model.SequencingRun import SequencingRun

import API


class Foo(object):

    """
    Class used to attach attributes
    """

    def __init__(self):
        pass


class TestApiCalls(unittest.TestCase):

    def setUp(self):

        print "\nStarting " + self.__module__ + ": " + self._testMethodName

    @patch("API.apiCalls.urlopen")
    @patch("API.apiCalls.ApiCalls.create_session")
    def test_validate_URL_existence_url_ok(self, mock_cs, mock_url):

        url_ok = Foo()
        setattr(url_ok, "code", httplib.OK)

        mock_url.side_effect = [url_ok]
        mock_cs.side_effect = [None]

        api = API.apiCalls.ApiCalls("", "", "", "", "")
        validate_URL = api.validate_URL_existence

        url = "http://google.com"
        valid = True

        is_valid = validate_URL(url)
        self.assertEqual(is_valid, valid)
        API.apiCalls.urlopen.assert_called_with(url, timeout=api.max_wait_time)

    @patch("API.apiCalls.urlopen")
    @patch("API.apiCalls.ApiCalls.create_session")
    def test_validate_URL_existence_url_raise_err(self, mock_cs, mock_url):

        url_raise_err = Foo()
        err_msg = "Unauthorized"
        setattr(url_raise_err, "code", httplib.UNAUTHORIZED)
        setattr(url_raise_err, "msg", err_msg)

        mock_url.side_effect = [url_raise_err]

        mock_cs.side_effect = [None]

        api = API.apiCalls.ApiCalls(
            client_id="",
            client_secret="",
            base_URL="",
            username="",
            password=""
        )

        validate_URL = api.validate_URL_existence

        url = "http://localhost:8080/api/"

        with self.assertRaises(Exception) as err:
            validate_URL(url)

        self.assertTrue(err_msg in str(err.exception))
        API.apiCalls.urlopen.assert_called_with(url, timeout=api.max_wait_time)

    @patch("API.apiCalls.urlopen")
    @patch("API.apiCalls.ApiCalls.create_session")
    def test_validate_URL_existence_url_not_found(self, mock_cs, mock_url):

        url_not_found = Foo()
        setattr(url_not_found, "code", httplib.NOT_FOUND)

        mock_url.side_effect = [url_not_found]
        mock_cs.side_effect = [None]

        api = API.apiCalls.ApiCalls("", "", "", "", "")
        validate_URL = api.validate_URL_existence

        url = "notAWebSite"
        valid = False

        is_valid = validate_URL(url)
        self.assertEqual(is_valid, valid)
        API.apiCalls.urlopen.assert_called_with(url, timeout=api.max_wait_time)

    @patch("API.apiCalls.ApiCalls.validate_URL_existence")
    @patch("API.apiCalls.ApiCalls.get_access_token")
    @patch("API.apiCalls.ApiCalls.get_oauth_service")
    @patch("API.apiCalls.validate_URL_form")
    def test_create_session_valid_base_url_no_slash(
            self, mock_validate_url_form,
            mock_get_oauth_service, mock_get_access_token,
            mock_validate_url_existence):

        oauth_service = Foo()
        access_token = Foo()
        setattr(oauth_service, "get_session", lambda x: "newSession1")

        mock_validate_url_form.side_effect = [True]
        mock_get_oauth_service.side_effect = [oauth_service]
        mock_get_access_token.side_effect = [access_token]
        mock_validate_url_existence.side_effect = [True]

        base_URL1 = "http://localhost:8080"
        api1 = API.apiCalls.ApiCalls(
            client_id="",
            client_secret="",
            base_URL=base_URL1,
            username="",
            password=""
        )

        mock_validate_url_existence.assert_called_with(
            base_URL1 + "/", use_session=True)

    @patch("API.apiCalls.ApiCalls.validate_URL_existence")
    @patch("API.apiCalls.ApiCalls.get_access_token")
    @patch("API.apiCalls.ApiCalls.get_oauth_service")
    @patch("API.apiCalls.validate_URL_form")
    def test_create_session_valid_base_url_slash(
            self, mock_validate_url_form,
            mock_get_oauth_service, mock_get_access_token,
            mock_validate_url_existence):

        oauth_service = Foo()
        access_token = Foo()
        setattr(oauth_service, "get_session", lambda x: "newSession2")

        mock_validate_url_form.side_effect = [True]
        mock_get_oauth_service.side_effect = [oauth_service]
        mock_get_access_token.side_effect = [access_token]
        mock_validate_url_existence.side_effect = [True]

        base_URL2 = "http://localhost:8080/"
        api2 = API.apiCalls.ApiCalls(
            client_id="",
            client_secret="",
            base_URL=base_URL2,
            username="",
            password=""
        )

        mock_validate_url_existence.assert_called_with(
            base_URL2, use_session=True)

    @patch("API.apiCalls.validate_URL_form")
    def test_create_session_invalid_form(self, mock_validate_url_form):

        mock_validate_url_form.side_effect = [False]

        base_URL = "invalidForm.com/"
        with self.assertRaises(URLError) as err:
            API.apiCalls.ApiCalls(
                client_id="",
                client_secret="",
                base_URL=base_URL,
                username="",
                password=""
            )

        self.assertTrue("not a valid URL" in str(err.exception))
        mock_validate_url_form.assert_called_with(base_URL)

    @patch("API.apiCalls.ApiCalls.validate_URL_existence")
    @patch("API.apiCalls.ApiCalls.get_access_token")
    @patch("API.apiCalls.ApiCalls.get_oauth_service")
    @patch("API.apiCalls.validate_URL_form")
    def test_create_session_invalid_session(self, mock_validate_url_form,
                                            mock_get_oauth_service,
                                            mock_get_access_token,
                                            mock_validate_url_existence):

        oauth_service = Foo()
        access_token = Foo()
        setattr(oauth_service, "get_session", lambda x: "newSession")

        mock_validate_url_form.side_effect = [True]
        mock_get_oauth_service.side_effect = [oauth_service]
        mock_get_access_token.side_effect = [access_token]
        mock_validate_url_existence.side_effect = [False]

        with self.assertRaises(Exception) as err:
            API.apiCalls.ApiCalls(
                client_id="",
                client_secret="",
                base_URL="",
                username="",
                password=""
            )

        expectedErrMsg = "Cannot create session. Verify your credentials " + \
            "are correct."

        self.assertTrue(expectedErrMsg in str(err.exception))
        mock_validate_url_form.assert_called_with("/")

    @patch("API.apiCalls.ApiCalls.create_session")
    @patch("API.apiCalls.ApiCalls.validate_URL_existence")
    def test_get_link_valid(self,
                            mock_validate_url_existence,
                            mock_cs):

        mock_validate_url_existence.side_effect = [True]
        mock_cs.side_effect = [None]

        api = API.apiCalls.ApiCalls(
            client_id="",
            client_secret="",
            base_URL="",
            username="",
            password=""
        )

        targ_URL = "http://localhost:8080/api/"
        targ_key = "project"
        targ_link = "http://localhost:8080/api/project"

        json_obj = {
            "resource": {
                "links": [
                        {
                            "rel": targ_key,
                            "href": targ_link
                        }
                ]
            }
        }

        session_response = Foo()
        setattr(session_response, "json", lambda: json_obj)

        session_get = MagicMock(side_effect=[session_response])
        session = Foo()
        setattr(session, "get", session_get)

        api.session = session
        link = api.get_link(targ_URL, targ_key)

        api.session.get.assert_called_with(targ_URL)
        self.assertEqual(link, targ_link)

    @patch("API.apiCalls.ApiCalls.create_session")
    @patch("API.apiCalls.ApiCalls.validate_URL_existence")
    def test_get_link_valid_targ_dict(self,
                                      mock_validate_url_existence,
                                      mock_cs):

        mock_validate_url_existence.side_effect = [True]
        mock_cs.side_effect = [None]

        api = API.apiCalls.ApiCalls(
            client_id="",
            client_secret="",
            base_URL="",
            username="",
            password=""
        )

        targ_URL = "http://localhost:8080/api/"
        targ_key = "project"
        targ_link = "http://localhost:8080/api/project"

        json_obj = {
            "resource": {
                "resources": [{
                    "identifier": "1",
                    "links": [
                        {
                            "rel": targ_key,
                            "href": targ_link
                        }
                    ]
                }]

            }
        }

        session_response = Foo()
        setattr(session_response, "json", lambda: json_obj)

        session_get = MagicMock(side_effect=[session_response])
        session = Foo()
        setattr(session, "get", session_get)

        api.session = session
        t_dict = {"key": "identifier", "value": "1"}
        link = api.get_link(targ_URL, targ_key, targ_dict=t_dict)

        api.session.get.assert_called_with(targ_URL)
        self.assertEqual(link, targ_link)

    @patch("API.apiCalls.ApiCalls.create_session")
    @patch("API.apiCalls.ApiCalls.validate_URL_existence")
    def test_get_link_invalid_url_not_found(self,
                                            mock_validate_url_existence,
                                            mock_cs):

        mock_validate_url_existence.side_effect = [False]
        mock_cs.side_effect = [None]

        api = API.apiCalls.ApiCalls(
            client_id="",
            client_secret="",
            base_URL="",
            username="",
            password=""
        )

        targ_URL = "http://localhost:8080/api/"
        targ_key = "project"

        with self.assertRaises(request_HTTPError) as err:
            api.get_link(targ_URL, targ_key)

        self.assertTrue("not a valid URL" in str(err.exception))
        mock_validate_url_existence.assert_called_with(targ_URL,
                                                       use_session=True)

    @patch("API.apiCalls.ApiCalls.create_session")
    @patch("API.apiCalls.ApiCalls.validate_URL_existence")
    def test_get_link_invalid_key_not_found(self,
                                            mock_validate_url_existence,
                                            mock_cs):

        mock_validate_url_existence.side_effect = [True]
        mock_cs.side_effect = [None]

        api = API.apiCalls.ApiCalls(
            client_id="",
            client_secret="",
            base_URL="",
            username="",
            password=""
        )

        targ_URL = "http://localhost:8080/api/"
        targ_key = "project"
        targ_link = "http://localhost:8080/api/project"
        invalid_key = "notProject"

        json_obj = {
            "resource": {
                "links": [
                        {
                            "rel": invalid_key,
                            "href": targ_link
                        }
                ]
            }
        }

        session_response = Foo()
        setattr(session_response, "json", lambda: json_obj)

        session_get = MagicMock(side_effect=[session_response])
        session = Foo()
        setattr(session, "get", session_get)

        api.session = session
        with self.assertRaises(KeyError) as err:
            api.get_link(targ_URL, targ_key)

        self.assertTrue(targ_key + " not found in links" in str(err.exception))
        self.assertTrue(
            "Available links: " + invalid_key in str(err.exception))
        api.session.get.assert_called_with(targ_URL)

    @patch("API.apiCalls.ApiCalls.create_session")
    @patch("API.apiCalls.ApiCalls.validate_URL_existence")
    def test_get_link_invalid_targ_dict_value(self,
                                              mock_validate_url_existence,
                                              mock_cs):

        mock_validate_url_existence.side_effect = [True]
        mock_cs.side_effect = [None]

        api = API.apiCalls.ApiCalls(
            client_id="",
            client_secret="",
            base_URL="",
            username="",
            password=""
        )

        targ_URL = "http://localhost:8080/api/"
        targ_key = "project"
        targ_link = "http://localhost:8080/api/project"

        json_obj = {
            "resource": {
                "resources": [{
                    "identifier": "1",
                    "links": [
                        {
                            "rel": targ_key,
                            "href": targ_link
                        }
                    ]
                }]

            }
        }

        session_response = Foo()
        setattr(session_response, "json", lambda: json_obj)

        session_get = MagicMock(side_effect=[session_response])
        session = Foo()
        setattr(session, "get", session_get)

        api.session = session
        t_dict = {"key": "identifier", "value": "2"}
        with self.assertRaises(KeyError) as err:
            api.get_link(targ_URL, targ_key, targ_dict=t_dict)

        self.assertTrue(t_dict["value"] + " not found." in str(err.exception))
        api.session.get.assert_called_with(targ_URL)

    @patch("API.apiCalls.ApiCalls.create_session")
    @patch("API.apiCalls.ApiCalls.validate_URL_existence")
    def test_get_link_invalid_targ_dict_key(self, mock_validate_url_existence,
                                            mock_cs):

        mock_validate_url_existence.side_effect = [True]
        mock_cs.side_effect = [None]

        api = API.apiCalls.ApiCalls(
            client_id="",
            client_secret="",
            base_URL="",
            username="",
            password=""
        )

        targ_URL = "http://localhost:8080/api/"
        targ_key = "project"
        targ_link = "http://localhost:8080/api/project"

        json_obj = {
            "resource": {
                "resources": [
                        {
                            "identifier": "1",
                            "links": [
                                {
                                    "rel": targ_key,
                                    "href": targ_link
                                }
                            ]
                        }
                ]
            }
        }

        session_response = Foo()
        setattr(session_response, "json", lambda: json_obj)

        session_get = MagicMock(side_effect=[session_response])
        session = Foo()
        setattr(session, "get", session_get)

        api.session = session
        t_dict = {"key": "notIdentifier", "value": "1"}
        with self.assertRaises(KeyError) as err:
            api.get_link(targ_URL, targ_key, targ_dict=t_dict)

        self.assertTrue(t_dict["key"] + " not found." in str(err.exception))
        self.assertTrue("Available keys: identifier" in str(err.exception))
        api.session.get.assert_called_with(targ_URL)

    @patch("API.apiCalls.ApiCalls.create_session")
    def test_get_projects_valid(self, mock_cs):

        mock_cs.side_effect = [None]

        api = API.apiCalls.ApiCalls(
            client_id="",
            client_secret="",
            base_URL="",
            username="",
            password=""
        )

        p1_dict = {
            "identifier": "1",
            "name": "project1",
            "projectDescription": ""
        }

        p2_dict = {
            "identifier": "2",
            "name": "project2",
            "projectDescription": "p2"
        }

        json_obj = {
            "resource": {
                "resources": [
                    p1_dict,
                    p2_dict
                ]
            }
        }

        session_response = Foo()
        setattr(session_response, "json", lambda: json_obj)

        session_get = MagicMock(side_effect=[session_response])
        session = Foo()
        setattr(session, "get", session_get)

        api.session = session
        api.get_link = lambda x, y: None

        proj_list = api.get_projects()
        self.assertEqual(len(proj_list), 2)

        self.assertEqual(proj_list[0].get_id(), p1_dict["identifier"])
        self.assertEqual(proj_list[0].get_name(), p1_dict["name"])
        self.assertEqual(proj_list[0].get_description(),
                         p1_dict["projectDescription"])

        self.assertEqual(proj_list[1].get_id(), p2_dict["identifier"])
        self.assertEqual(proj_list[1].get_name(), p2_dict["name"])
        self.assertEqual(proj_list[1].get_description(),
                         p2_dict["projectDescription"])

    @patch("API.apiCalls.ApiCalls.create_session")
    def test_get_projects_invalid_missing_key(self, mock_cs):

        mock_cs.side_effect = [None]

        api = API.apiCalls.ApiCalls(
            client_id="",
            client_secret="",
            base_URL="",
            username="",
            password=""
        )

        p1_dict = {
            "identifier": "1",

            "projectDescription": ""
        }

        p2_dict = {
            "identifier": "2",

            "projectDescription": "p2"
        }

        json_obj = {
            "resource": {
                "resources": [
                    p1_dict,
                    p2_dict
                ]
            }
        }

        session_response = Foo()
        setattr(session_response, "json", lambda: json_obj)

        session_get = MagicMock(side_effect=[session_response])
        session = Foo()
        setattr(session, "get", session_get)

        api.session = session
        api.get_link = lambda x, y: None

        with self.assertRaises(KeyError) as err:
            api.get_projects()

        self.assertTrue("name not found" in str(err.exception))
        self.assertTrue("Available keys: projectDescription, identifier"
                        in str(err.exception))

    @patch("API.apiCalls.ApiCalls.create_session")
    def test_get_samples_valid(self, mock_cs):

        mock_cs.side_effect = [None]

        api = API.apiCalls.ApiCalls(
            client_id="",
            client_secret="",
            base_URL="",
            username="",
            password=""
        )

        sample_dict = {
            "sequencerSampleId": "03-3333",
            "description": "The 53rd sample",
            "sampleName": "03-3333",
            "identifier": "1"
        }

        json_obj = {
            "resource": {
                "resources": [
                    sample_dict
                ]
            }
        }

        session_response = Foo()
        setattr(session_response, "json", lambda: json_obj)

        session_get = MagicMock(side_effect=[session_response])
        session = Foo()
        setattr(session, "get", session_get)

        api.session = session
        api.get_link = lambda x, y, targ_dict="": None

        proj = API.apiCalls.Project("project1", "projectDescription", "1")
        sample_list = api.get_samples(proj)

        self.assertEqual(len(sample_list), 1)
        self.assertEqual(sample_dict.items(),
                         sample_list[0].get_dict().items())

    @patch("API.apiCalls.ApiCalls.create_session")
    def test_get_samples_invalid_proj_id(self, mock_cs):

        mock_cs.side_effect = [None]

        api = API.apiCalls.ApiCalls(
            client_id="",
            client_secret="",
            base_URL="",
            username="",
            password=""
        )

        api.get_link = MagicMock(side_effect=[StopIteration])

        proj = API.apiCalls.Project("project1", "projectDescription", "999")

        with self.assertRaises(API.apiCalls.ProjectError) as err:
            api.get_samples(proj)

        self.assertTrue(proj.get_id() + " doesn't exist"
                        in str(err.exception))

    @patch("API.apiCalls.ApiCalls.create_session")
    def test_get_sequence_files_valid(self, mock_cs):

        mock_cs.side_effect = [None]

        api = API.apiCalls.ApiCalls(
            client_id="",
            client_secret="",
            base_URL="",
            username="",
            password=""
        )

        seq_dict = {
            "file": "/tmp/sequence-files/12/2/03-3333_S1_L001_R2_001.fastq",
            "fileName": "03-3333_S1_L001_R2_001.fastq",
            "identifier": "12",
            "links": [{
                    "rel": "self",
                    "href": "http://localhost:8080/api/" +
                    "projects/4/samples/53/sequenceFiles/12"
            }]
        }

        json_obj = {
            "resource": {
                "resources": [
                    seq_dict
                ]
            }
        }

        session_response = Foo()
        setattr(session_response, "json", lambda: json_obj)

        session_get = MagicMock(side_effect=[session_response])
        session = Foo()
        setattr(session, "get", session_get)

        api.session = session
        api.get_link = lambda x, y, targ_dict="": None

        sample_dict = {
            "sequencerSampleId": "03-3333",
            "description": "The 53rd sample",
            "sampleName": "03-3333",
            "sampleProject": "1"
        }

        sample = API.apiCalls.Sample(sample_dict)
        seqRes = api.get_sequence_files(sample)

        self.assertEqual(len(seqRes), 1)
        self.assertEqual(seq_dict.items(), seqRes[0].items())

    @patch("API.apiCalls.ApiCalls.create_session")
    def test_get_sequence_files_invalid_proj(self, mock_cs):

        mock_cs.side_effect = [None]

        api = API.apiCalls.ApiCalls(
            client_id="",
            client_secret="",
            base_URL="",
            username="",
            password=""
        )

        api.get_link = MagicMock(side_effect=[StopIteration])

        sample = API.apiCalls.Sample({"sampleProject": "999", "sampleName": "1"})

        with self.assertRaises(API.apiCalls.ProjectError) as err:
            api.get_sequence_files(sample)

        self.assertTrue(sample["sampleProject"] + " doesn't exist"
                        in str(err.exception))

    @patch("API.apiCalls.ApiCalls.create_session")
    def test_get_sequence_files_invalid_sample(self, mock_cs):

        mock_cs.side_effect = [None]

        api = API.apiCalls.ApiCalls(
            client_id="",
            client_secret="",
            base_URL="",
            username="",
            password=""
        )
        # proj_URL, sample_URL, url->sample/sequenceFiles
        api.get_link = MagicMock(side_effect=[None, None, StopIteration])

        sample_dict = {
            "sequencerSampleId": "03-3333",
            "description": "The 53rd sample",
            "sampleName": "03-3333",
            "sampleProject": "999"
        }

        sample = API.apiCalls.Sample(sample_dict)

        with self.assertRaises(API.apiCalls.SampleError) as err:
            api.get_sequence_files(sample)

        self.assertTrue(sample.get_id() + " doesn't exist"
                        in str(err.exception))

    @patch("API.apiCalls.ApiCalls.create_session")
    def test_send_project_valid(self, mock_cs):

        mock_cs.side_effect = [None]

        api = API.apiCalls.ApiCalls(
            client_id="",
            client_secret="",
            base_URL="",
            username="",
            password=""
        )

        json_dict = {
            "resource": {
                "name": "project1",
                "projectDescription": "projectDescription",
                "identifier": "1"
            }
        }

        json_obj = json.dumps(json_dict)

        session_response = Foo()
        setattr(session_response, "status_code", httplib.CREATED)
        setattr(session_response, "text", json_obj)

        session_post = MagicMock(side_effect=[session_response])
        session = Foo()
        setattr(session, "post", session_post)

        api.session = session
        api.get_link = lambda x, y, targ_dict="": None
        proj = API.apiCalls.Project("project1", "projectDescription", "1")

        json_res = api.send_project(proj)
        self.assertEqual(json_dict, json_res)

    @patch("API.apiCalls.ApiCalls.create_session")
    def test_send_project_invalid_name(self, mock_cs):

        mock_cs.side_effect = [None]

        api = API.apiCalls.ApiCalls(
            client_id="",
            client_secret="",
            base_URL="",
            username="",
            password=""
        )

        proj = API.apiCalls.Project("p", "projectDescription", "1")

        with self.assertRaises(API.apiCalls.ProjectError) as err:
            api.send_project(proj)

        self.assertTrue("Invalid project name: " + proj.get_name() in
                        str(err.exception))
        self.assertTrue("A project requires a name that must be" +
                        " 5 or more characters" in str(err.exception))

    @patch("API.apiCalls.ApiCalls.create_session")
    def test_send_project_invalid_server_res(self, mock_cs):

        mock_cs.side_effect = [None]

        api = API.apiCalls.ApiCalls(
            client_id="",
            client_secret="",
            base_URL="",
            username="",
            password=""
        )

        session_response = Foo()
        setattr(session_response, "status_code", httplib.INTERNAL_SERVER_ERROR)
        setattr(session_response, "text", "Server unavailable")

        session_post = MagicMock(side_effect=[session_response])
        session = Foo()
        setattr(session, "post", session_post)

        api.session = session
        api.get_link = lambda x, y, targ_dict="": None

        proj = API.apiCalls.Project("project1", "projectDescription", "1")

        with self.assertRaises(API.apiCalls.ProjectError) as err:
            api.send_project(proj)

        self.assertTrue(str(session_response.status_code) + " " +
                        session_response.text in str(err.exception))

    @patch("API.apiCalls.ApiCalls.create_session")
    def test_send_samples_valid(self, mock_cs):

        mock_cs.side_effect = [None]

        api = API.apiCalls.ApiCalls(
            client_id="",
            client_secret="",
            base_URL="",
            username="",
            password=""
        )

        json_dict = {
            "resource": {
                "sequencerSampleId": "03-3333",
                "description": "The 53rd sample",
                "sampleName": "03-3333",
                "sampleProject": "1"
            }
        }

        json_obj = json.dumps(json_dict)

        session_response = Foo()
        setattr(session_response, "status_code", httplib.CREATED)
        setattr(session_response, "text", json_obj)

        session_post = MagicMock(side_effect=[session_response])
        session = Foo()
        setattr(session, "post", session_post)

        api.get_link = lambda x, y, targ_dict="": None
        api.session = session

        sample_dict = {
            "sequencerSampleId": "03-3333",
            "description": "The 53rd sample",
            "sampleName": "03-3333",
            "sampleProject": "1"
        }

        sample = API.apiCalls.Sample(sample_dict)
        json_res_list = api.send_samples([sample])

        self.assertEqual(len(json_res_list), 1)

        json_res = json_res_list[0]
        self.assertEqual(json_res, json_dict)

    @patch("API.apiCalls.ApiCalls.create_session")
    def test_send_samples_invalid_proj_id(self, mock_cs):

        mock_cs.side_effect = [None]

        api = API.apiCalls.ApiCalls(
            client_id="",
            client_secret="",
            base_URL="",
            username="",
            password=""
        )

        api.get_link = MagicMock(side_effect=[StopIteration])

        proj_id = "-1"
        sample = API.apiCalls.Sample({"sampleProject": proj_id, "sampleName": "1"})

        with self.assertRaises(API.apiCalls.ProjectError) as err:
            api.send_samples([sample])

        self.assertTrue(proj_id + " doesn't exist"
                        in str(err.exception))

    @patch("API.apiCalls.ApiCalls.create_session")
    def test_send_samples_invalid_server_res(self, mock_cs):

        mock_cs.side_effect = [None]

        api = API.apiCalls.ApiCalls(
            client_id="",
            client_secret="",
            base_URL="",
            username="",
            password=""
        )

        metadata_dict = {
            "workflow": "test_workflow",
            "readLengths": "1",
            "layoutType": "PAIRED_END"
        }
        run_on_server = api.create_seq_run(metadata_dict)

        session_response = Foo()
        setattr(session_response, "status_code", httplib.CONFLICT)
        setattr(session_response, "text",
                "An entity already exists with that identifier")

        session_post = MagicMock(side_effect=[session_response])
        session = Foo()
        setattr(session, "post", session_post)

        api.session = session
        api.get_link = lambda x, y, targ_dict="": None
        sample = API.apiCalls.Sample({"sampleProject": "1", "run": run_on_server, "sampleName": "123"})

        with self.assertRaises(API.apiCalls.SampleError) as err:
            api.send_samples([sample])

        self.assertTrue(str(session_response.status_code) + ": " +
                        session_response.text in str(err.exception))

    @patch("API.apiCalls.ApiCalls.create_session")
    @patch("os.path.getsize")
    def test_send_sequence_files_valid(self, getsize, mock_cs):

        mock_cs.side_effect = [None]

        api = API.apiCalls.ApiCalls(
            client_id="",
            client_secret="",
            base_URL="",
            username="",
            password=""
        )

        json_dict = {
            "resource": [
                {
                    "file": "03-3333_S1_L001_R1_001.fastq.gz"
                },
                {
                    "file": "03-3333_S1_L001_R2_001.fastq.gz"
                }
            ]
        }

        json_obj = json.dumps(json_dict)

        session_response = Foo()
        setattr(session_response, "status_code", httplib.CREATED)
        setattr(session_response, "text", json_obj)

        session_post = MagicMock(side_effect=[session_response])
        session = Foo()
        setattr(session, "post", session_post)

        api.get_link = lambda x, y, targ_dict="": None
        api.session = session
        API.apiCalls.ApiCalls.get_file_size_list = MagicMock()

        sample_dict = {
            "sequencerSampleId": "03-3333",
            "description": "The 53rd sample",
            "sampleName": "03-3333",
            "sampleProject": "1"
        }

        sample = API.apiCalls.Sample(sample_dict)
        files = ["03-3333_S1_L001_R1_001.fastq.gz",
                      "03-3333_S1_L001_R2_001.fastq.gz"]
        seq_file = SequenceFile({}, files)
        sample.set_seq_file(seq_file)
    	sample.run = SequencingRun(sample_sheet="sheet", sample_list=[sample])
    	sample.run._sample_sheet_name = "sheet"

        kwargs = {
            "samples_list": [sample]
        }
        json_res_list = api.send_sequence_files(**kwargs)

        self.assertEqual(len(json_res_list), 1)

        json_res = json_res_list[0]
        self.assertEqual(json_res, json_dict)

    @patch("API.apiCalls.ApiCalls.create_session")
    def test_send_sequence_files_invalid_proj_id(self, mock_cs):

        mock_cs.side_effect = [None]

        api = API.apiCalls.ApiCalls(
            client_id="",
            client_secret="",
            base_URL="",
            username="",
            password=""
        )

        api.get_link = MagicMock(side_effect=[StopIteration])
        api.get_file_size_list = MagicMock()

        proj_id = "-1"
        sample = API.apiCalls.Sample({"sampleProject": proj_id, "sampleName": "sample"})
        seq_file = SequenceFile({}, [])
        sample.set_seq_file(seq_file)
        sample.run = SequencingRun(sample_sheet="sheet", sample_list=[sample])
    	sample.run._sample_sheet_name = "sheet"

        with self.assertRaises(API.apiCalls.ProjectError) as err:
            api.send_sequence_files([sample])

        self.assertIn("project ID: {proj_id} doesn't exist".format(
            proj_id=proj_id), str(err.exception))

    @patch("API.apiCalls.ApiCalls.create_session")
    def test_send_sequence_files_invalid_sample_id(self, mock_cs):

        mock_cs.side_effect = [None]

        api = API.apiCalls.ApiCalls(
            client_id="",
            client_secret="",
            base_URL="",
            username="",
            password=""
        )

        api.get_link = MagicMock(side_effect=[None, None, StopIteration])
        api.get_file_size_list = MagicMock()

        proj_id = "1"
        sample_id = "-1"
        sample = API.apiCalls.Sample({
            "sampleProject": proj_id,
            "sampleName": sample_id,
            "sequencerSampleId": sample_id
        })
        seq_file = SequenceFile({}, [])
        sample.set_seq_file(seq_file)
        sample.run = SequencingRun(sample_sheet="sheet", sample_list=[sample])
    	sample.run._sample_sheet_name = "sheet"

        with self.assertRaises(API.apiCalls.SampleError) as err:
            api.send_sequence_files([sample])

        self.assertIn("sample ID: {sample_id} doesn't exist".format(
            sample_id=sample_id), str(err.exception))
