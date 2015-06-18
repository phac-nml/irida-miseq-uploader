from Tests.unitTests.test_OfflineValidation import offValidationTestSuite
from Tests.unitTests.test_MiseqParser import parserTestSuite
from Tests.unitTests.test_ApiCalls import api_TestSuite
from Tests.integrationTests.test_ApiCalls_integration import api_integration_TestSuite
from sys import argv
import unittest

"""
For running all tests or commenting out particular tests suites to only run selected tests.
"""

if __name__=="__main__":
	suiteList=[]


	suiteList.append(offValidationTestSuite)
	suiteList.append(parserTestSuite)
	suiteList.append(api_TestSuite)
	suiteList.append(api_integration_TestSuite)


	fullSuite = unittest.TestSuite(suiteList)

	runner = unittest.TextTestRunner()
	runner.run(fullSuite)
