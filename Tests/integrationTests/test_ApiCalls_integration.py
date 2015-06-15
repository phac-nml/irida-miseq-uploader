import unittest
import sys
sys.path.append("../../")
from ConfigParser import RawConfigParser
from os import path

from API.apiCalls import ApiCalls


path_to_module=path.dirname(__file__)
if len(path_to_module)==0:
	path_to_module="."

conf_Parser=RawConfigParser()
conf_Parser.read(path.join(path_to_module,"..","..","config.conf"))

client_id=conf_Parser.get("apiCalls","client_id")
client_secret=conf_Parser.get("apiCalls","client_secret")
base_URL="http://localhost:8080/api"
username="admin"
password="password1"

class TestApiIntegration(unittest.TestCase):

	def setUp(self):

		print "\nStarting ", self._testMethodName

	def test_connect_and_authenticate(self):

		apiCalls=ApiCalls(
			client_id=client_id,
			client_secret=client_secret,
			base_URL=base_URL,
			username=username,
			password=password
		)


api_integration_TestSuite = unittest.TestSuite()
api_integration_TestSuite.addTest(TestApiIntegration("test_connect_and_authenticate"))

if __name__=="__main__":
	suiteList=[]

	suiteList.append(api_integration_TestSuite)
	fullSuite = unittest.TestSuite(suiteList)

	runner = unittest.TextTestRunner()
	runner.run(fullSuite)
