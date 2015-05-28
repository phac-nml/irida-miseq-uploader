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
from urllib2 import URLError, urlopen
from rauth import OAuth2Service

def deadFunc(*args, **kwargs):
	pass

class TestApiCalls(unittest.TestCase):



	def setUp(self):
		print "\nStarting ", self._testMethodName
		self.mock=None

		#uncomment this to disable mocking. effect example: API.apiCalls.validateURL in test_validateURL will be actually making http connections/requests to the URLs that it's given.
		self.setUpMock=self.setUpMockDisabled

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

	def test_validateURL(self):
		"""
			replace the urlopen() being called in API.apiCalls.validateURL() with a mock/fake object
			the side_effect being set to raisedErrorsList makes this object return one of these items per call to this function. They are returned in the same order (FIFO).
			The items inside raisedErrorsList match the items in uDict (i.e.
			http://validURL.com raises no errors (None),
			'www.noscheme.com' raises ValueError,
			http://validURL.com/invalidPath raises URLError)

			This tests for how these errors are handled when they are raised but it doesn't test that http://validURL.com/invalidPath will cause an URLError when used as an argument for urlopen because it's mocked and no actual connection/request is sent in this test.
		"""


		validateURL=API.apiCalls.validateURL

		raisedErrorsList=[
			None,
			ValueError(""),
			URLError("")
		]

		API.apiCalls.urlopen=self.setUpMock(urlopen, raisedErrorsList)


		#link : tuple of expected results
		urlList=[
			{"url":"http://google.com",
			"valid":True, "msg":"No error messages"},

			{"url":"www.google.com",
			"valid":False, "msg":"URL must include scheme"},

			{"url":"http://google.com/invalidPath",
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

		username="admin"
		password="password1"

		raisedErrorsList=[
			None,
			Exception,
			Exception
		]
		urlList=[
			{"url":"http://localhost:8080/api/",
			"valid":True, "msg":"No error messages"},

			{"url":"http://localhost:8080/api",
			"valid":False, "msg":"URL must include scheme"},

			{"url":"http://notasite.1",
			"valid":False, "msg":"Failed to reach a server"}
		]
		for i in range(0,len(urlList)):
			item= urlList[i]

			print item["url"]


			session=createSession(item["url"], username, password)
			print session


	def test_getProjects(self):
		createSession=API.apiCalls.createSession
		getProjects=API.apiCalls.getProjects

		#baseURL="http://localhost:8080/api/"
		baseURL="http://feowmf.com/api"
		username="admin"
		password="password1"

		session=createSession(baseURL, username, password)
		#projList=getProjects(session, baseURL)

		#API.apiCalls.OAuth2Service=self.setUpMock(OAuth2Service)


api_TestSuite= unittest.TestSuite()
#api_TestSuite.addTest( TestApiCalls("test_validateURL") )
#api_TestSuite.addTest( TestApiCalls("test_getProjects") )
api_TestSuite.addTest( TestApiCalls("testCreateSession") )

if __name__=="__main__":
	suiteList=[]

	suiteList.append(api_TestSuite)
	fullSuite = unittest.TestSuite(suiteList)

	runner = unittest.TextTestRunner()
	runner.run(fullSuite)
