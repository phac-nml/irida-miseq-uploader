import unittest
import json
import httplib
from sys import path, argv
path.append("../../")
from urllib2 import URLError, urlopen, HTTPError

from mock import patch, MagicMock
from rauth import OAuth2Service
from rauth.session import OAuth2Session
from requests.exceptions import HTTPError as request_HTTPError
from requests.models import Response

import API.apiCalls

class Foo(object):
	"""
	Class used to attach attributes
	"""
	def __init__(self):
		pass

class TestApiCalls(unittest.TestCase):

	def setUp(self):

		print "\nStarting ", self._testMethodName

	@patch("API.apiCalls.urlopen")
	@patch("API.apiCalls.ApiCalls.create_session")
	def test_validate_URL_existence(self, mock_cs, mock_url):

		"""
		replace the urlopen() being called in ApiCalls.validate_URL_existence() with a mock/fake object.
		The side_effect being set to urlOpenResults makes the mock object return one of these items per call to this function. They are returned in the same order (FIFO).
		The items inside raisedErrorsList match the items in uDict (i.e.
		http://google.com/ returns urlOpenOk,
		http://localhost:8080/api/ urlOpenRaise ,
		notAWebSite returns urlOpenNotFound)
		"""

		url_ok = Foo()
		url_raise_err = Foo()
		url_not_found = Foo()
		err_msg = "Unauthorized"
		setattr(url_ok,"code", httplib.OK)
		setattr(url_raise_err, "code", httplib.UNAUTHORIZED)
		setattr(url_raise_err, "msg", err_msg)
		setattr(url_not_found, "code", httplib.NOT_FOUND)

		urlopen_results=[
			url_ok,
			url_raise_err,
			url_not_found
		]

		mock_url.side_effect = urlopen_results
		mock_cs.side_effect = [None]

		api = API.apiCalls.ApiCalls("","","","","")
		validate_URL = api.validate_URL_existence

		url_List=[
			{"url":"http://google.com",
			"valid":True},

			{"url":"http://localhost:8080/api/",
			"assertion":Exception, "msg":err_msg, "valid":False},

			{"url":"notAWebSite",
			"valid":False}
		]

		for item in url_List:

			if item.has_key("assertion"):
				with self.assertRaises(item["assertion"]) as err:
					isValid = validate_URL(item["url"])

				self.assertTrue(item["msg"] in str(err.exception))

			else:
				isValid=validate_URL( item["url"] )
				self.assertEqual(isValid, item["valid"])

			API.apiCalls.urlopen.assert_called_with( item["url"], timeout=api.max_wait_time)

	@patch("API.apiCalls.ApiCalls.validate_URL_existence")
	@patch("API.apiCalls.ApiCalls.get_access_token")
	@patch("API.apiCalls.ApiCalls.get_oauth_service")
	@patch("API.apiCalls.validate_URL_Form")
	def test_create_session_valid(self, mock_validate_url_form,
								mock_get_oauth_service, mock_get_access_token,
								mock_validate_url_existence):

		oauth_service=Foo()
		access_token=Foo()
		setattr(oauth_service, "get_session", lambda x: "newSession")

		mock_validate_url_form.side_effect = [True]*2
		mock_get_oauth_service.side_effect = [oauth_service]*2
		mock_get_access_token.side_effect = [access_token]*2
		mock_validate_url_existence.side_effect=[True]*2


		base_URL1="http://localhost:8080"
		api=API.apiCalls.ApiCalls(
		  client_id="",
		  client_secret="",
		  base_URL=base_URL1,
		  username="",
		  password=""
		)

		self.assertEqual(api.session, oauth_service.get_session(access_token))
		mock_validate_url_existence.assert_called_with(base_URL1 + "/", use_session=True)


		base_URL2="http://localhost:8080/"
		api=API.apiCalls.ApiCalls(
		  client_id="",
		  client_secret="",
		  base_URL=base_URL2,
		  username="",
		  password=""
		)

		self.assertEqual(api.session, oauth_service.get_session(access_token))
		mock_validate_url_existence.assert_called_with(base_URL2, use_session=True)

	def test_getProjects(self):

		createSession=API.apiCalls.createSession
		getProjects=API.apiCalls.getProjects

		baseURL="http://localhost:8080/api/"
		username="admin"
		password="password1"

		API.apiCalls.urlopen=self.setUpMock(urlopen)

		session=createSession(baseURL, username, password)

		projectLinkResponse=OAuth2Session('123','456', access_token='321')
		projectsListResponse=OAuth2Session('123','456', access_token='321')

		projectLinkJson={u'resource':{u'links':[{'rel':u'projects',u'href':u'http://localhost:8080/api/projects'}]}}
		projectsListJson={u'resource':{u'resources': [{u'projectDescription': None, u'identifier': u'1', u'name': u'Project1',u'createdDate':1432050859000},{u'projectDescription': None, u'identifier': u'2', u'name':u'Project 3', u'createdDate':1432050853000}]}, u'links':[		{'rel':u'projects',u'href':u'http://localhost:8080/api/projects'}]}

		setattr(projectLinkResponse,"json", lambda : projectLinkJson)#lambda returns function - since json attribute will be a callable function (i.e mockResponse.json() instead of mockResponse.json)
		setattr(projectLinkResponse,"status_code", httplib.OK)
		setattr(projectsListResponse,"json", lambda : projectsListJson)
		setattr(projectsListResponse,"status_code", httplib.OK)

		funcHolder=API.apiCalls.OAuth2Session.get
		API.apiCalls.OAuth2Session.get=self.setUpMock(OAuth2Session.get, [projectLinkResponse, projectsListResponse] )

		projList=getProjects(session, baseURL)

		if self.mocking==True:#only test if mocking enabled since irida server actually returns number of projects (>100)
			API.apiCalls.OAuth2Session.get.assert_called_with(projectLinkJson["resource"]["links"][0]["href"])
			self.assertEqual(len(projList), 2)
			projNames= [ proj["name"] for proj in projList ]
			expectedRes= [ proj["name"] for proj in projectsListJson["resource"]["resources"] ]
			self.assertEqual(projNames, expectedRes)


		expectedKeys=set( ("name","projectDescription") )
		for proj in projList:
			self.assertTrue( all([key in proj.keys() for key in expectedKeys]))

		API.apiCalls.OAuth2Session.get=funcHolder


	def test_sendProjects_valid(self):
		createSession=API.apiCalls.createSession
		sendProjects=API.apiCalls.sendProjects

		baseURL="http://localhost:8080/api/"
		username="admin"
		password="password1"
		headers = {'headers': {'Content-Type':'application/json'}}

		mockResponse=OAuth2Session('123','456', access_token='321')
		expectedDict={
			"resource":
			{
				"projectDescription" : "This is a test project",
				"name" : "testProject",
				"identifier" : "123",
				"createdDate" : 1433173545000
			}
		}

		jsonResponse=json.dumps(expectedDict)
		setattr(mockResponse,"text", jsonResponse)
		setattr(mockResponse,"status_code", httplib.CREATED)

		API.apiCalls.urlopen=self.setUpMock(urlopen)

		funcHolder=API.apiCalls.OAuth2Session.post
		API.apiCalls.OAuth2Session.post=self.setUpMock(API.apiCalls.OAuth2Session.post, [mockResponse] )

		session=createSession(baseURL, username, password)

		projToSend= {"name":"testProject", "projectDescription": "This is a test project"}
		res=sendProjects(session , baseURL, projToSend)

		if self.mocking==True:
			API.apiCalls.OAuth2Session.post.assert_called_with(baseURL+"projects", json.dumps(projToSend), **headers  )

		#check that names and project descriptions are the same
		for key in projToSend.keys():
			self.assertEqual(res["resource"][key], expectedDict["resource"][key])

		API.apiCalls.OAuth2Session.post=funcHolder


	def test_sendProjects_invalid(self):
		createSession=API.apiCalls.createSession
		sendProjects=API.apiCalls.sendProjects

		baseURL="http://localhost:8080/api/"
		username="admin"
		password="password1"
		headers = {'headers': {'Content-Type':'application/json'}}

		mockResponse=OAuth2Session('123','456', access_token='321')
		jsonResponse=json.dumps(
		{
			"resource":
			{
				"projectDescription" : "This is a test project",
				"name" : "testProject",
				"identifier" : "123",
				"createdDate" : 1433173545000
			}
		})
		setattr(mockResponse,"text", jsonResponse)
		setattr(mockResponse,"status_code", httplib.CREATED)

		API.apiCalls.urlopen=self.setUpMock(urlopen)

		funcHolder=API.apiCalls.OAuth2Session.post
		API.apiCalls.OAuth2Session.post=self.setUpMock(API.apiCalls.OAuth2Session.post, [mockResponse] )

		session=createSession(baseURL, username, password)

		projToSend= {"projectDescription": "This project has no name"}

		with self.assertRaises(API.apiCalls.ProjectError) as context:
			res=sendProjects(session , baseURL, projToSend)

		self.assertTrue("Missing project name" in str(context.exception))

		if self.mocking==True:
			assert not API.apiCalls.OAuth2Session.post.called

		API.apiCalls.OAuth2Session.post=funcHolder


api_TestSuite= unittest.TestSuite()
api_TestSuite.addTest( TestApiCalls("test_validate_URL_existence") )
api_TestSuite.addTest( TestApiCalls("test_create_session_valid") )
#api_TestSuite.addTest( TestApiCalls("test_getProjects") )
#api_TestSuite.addTest( TestApiCalls("test_sendProjects_valid") )
#api_TestSuite.addTest( TestApiCalls("test_sendProjects_invalid") )

if __name__=="__main__":
	suiteList=[]

	suiteList.append(api_TestSuite)
	fullSuite = unittest.TestSuite(suiteList)

	runner = unittest.TextTestRunner()
	runner.run(fullSuite)
