import unittest
import sys

sys.path.append("../../")
from os import path

#https://pypi.python.org/pypi/mock#downloads
#Download mock-1.0.1.tar.gz
#extract
#cd mock-1.0.1
#sudo python setup.py build
#sudo python setup.py install

import API.apiCalls
from mock import patch, MagicMock
from urllib2 import URLError, urlopen, HTTPError
from rauth import OAuth2Service
from rauth.session import OAuth2Session
from requests.exceptions import HTTPError as request_HTTPError
from requests.models import Response

def deadFunc(*args, **kwargs):
	""" placeholder function that takes in arguments and does nothing. used to disable functions that are associated with Mock/MagicMock objects
	"""
	pass

class TestApiCalls(unittest.TestCase):



	def setUp(self):
		print "\nStarting ", self._testMethodName
		self.mock=None

		#uncomment this to disable mocking. effect example: API.apiCalls.validateURL in test_validateURL will be actually making http connections/requests to the URLs that it's given.
		#self.setUpMock=self.setUpMockDisabled

	def setUpMockDisabled(self, func, nse=[]):
		print "Mock disabled"

		func.assert_called_with=deadFunc
		return func


	def setUpMock(self, func, newSideEffect=[]):
		print "Mock enabled"
		if len(newSideEffect)>0:
			self.mock=MagicMock(side_effect=newSideEffect)
		else:
			self.mock=MagicMock()

		return self.mock

	def test_validateURLexistance(self):
		"""
			replace the urlopen() being called in API.apiCalls.validateURLexistance() with a mock/fake object
			the side_effect being set to raisedErrorsList makes this object return one of these items per call to this function. They are returned in the same order (FIFO).
			The items inside raisedErrorsList match the items in uDict (i.e.
			http://google.com/ raises no errors (None),
			http://localhost:8080/api/ raises no errors (None),
			http://google.com/invalidPath/ raises HTTPError)

			This tests for how these errors are handled when they are raised but it doesn't test that http://google.com/invalidPath/ will cause an HTTPError when used as an argument for urlopen because it's mocked and no actual connection/request is sent in this test.
			Disabling mock in setUp will show that http://google.com/invalidPath/ does raise an HTTPError
		"""


		validateURL=API.apiCalls.validateURLexistance

		raisedErrorsList=[
			None,
			None,
			HTTPError(url="http://google.com/invalidPath/",code=404,msg="Not found",hdrs="None",fp=None)
		]

		API.apiCalls.urlopen=self.setUpMock(urlopen, raisedErrorsList)


		urlList=[
			{"url":"http://google.com/",
			"valid":True, "msg":"No error messages"},

			{"url":"http://localhost:8080/api/",
			"valid":True, "msg":"No error messages"},

			{"url":"http://google.com/invalidPath/",
			"valid":False, "msg":"Failed to reach"}
		]

		for item in urlList:

			vRes=validateURL( item["url"] )

			API.apiCalls.urlopen.assert_called_with( item["url"], timeout=API.apiCalls.MAX_TIMEOUT_WAIT)
			#When mocking enabled, asserts that the urlopen function inside API.apiCalls.validateURL was called with item["url"] as an argument

			self.assertEqual(vRes.isValid(), item["valid"] )

			self.assertTrue( item["msg"] in vRes.getErrors() )

	def testCreateSession(self):
		createSession=API.apiCalls.createSession

		#URLError is raised by the validateURLForm so not included here
		raisedErrorsList=[
			None,
			HTTPError(url="http://google.com/invalidPath/",code=404,msg="Not found",hdrs="None",fp=None)
		]

		API.apiCalls.urlopen=self.setUpMock(urlopen, raisedErrorsList)


		urlList=[
			{"url":"http://localhost:8080/api/",
			"valid":True, "msg":"No error messages","assertion":None},

			{"url":"http://localhost:8080/api",
			"valid":False, "msg":"URL must end with '/'","assertion":URLError},

			{"url":"http://google.com/invalidPath/",
			"valid":False, "msg":"Failed to reach","assertion":request_HTTPError}
		]

		username="admin"
		password="password1"

		for i in range(0,len(urlList)):
			item= urlList[i]


			if item["assertion"]!=None:
				print item["assertion"]
				with self.assertRaises(item["assertion"]) as errMsg:
					createSession(item["url"], username, password)


				self.assertTrue( item["msg"] in str(errMsg.exception) )


			else:
				session=createSession(item["url"], username, password)
				API.apiCalls.urlopen.assert_called_with(item["url"]+"oauth/token", timeout=API.apiCalls.MAX_TIMEOUT_WAIT)



	def test_getProjects(self):
		createSession=API.apiCalls.createSession
		getProjects=API.apiCalls.getProjects

		baseURL="http://localhost:8080/api/"
		username="admin"
		password="password1"

		raisedErrorsList=[None, None]

		API.apiCalls.urlopen=self.setUpMock(urlopen, raisedErrorsList)

		session=createSession(baseURL, username, password)
		o2=OAuth2Session('123','456', access_token='321')

		jsonResponse={u'resource': {u'resources': [{u'projectDescription': None, u'identifier': u'1', u'name': u'Project 1', u'createdDate': 1432050859000}, {u'projectDescription': None, u'identifier': u'2', u'name': u'Project 3',u'createdDate': 1432050859000} ]}}
		setattr(o2,"json", lambda : jsonResponse)
		API.apiCalls.OAuth2Session.get=self.setUpMock(OAuth2Session.get, [o2] )

		projList=getProjects(session, baseURL)
		self.assertEqual(len(projList), 2)



api_TestSuite= unittest.TestSuite()
api_TestSuite.addTest( TestApiCalls("test_validateURLexistance") )
api_TestSuite.addTest( TestApiCalls("test_getProjects") )
api_TestSuite.addTest( TestApiCalls("testCreateSession") )

if __name__=="__main__":
	suiteList=[]

	suiteList.append(api_TestSuite)
	fullSuite = unittest.TestSuite(suiteList)

	runner = unittest.TextTestRunner()
	runner.run(fullSuite)
