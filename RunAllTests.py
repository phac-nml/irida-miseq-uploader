from Tests.unitTests.testOfflineValidation import offValidationTestSuite
from Tests.unitTests.testMiseqParser import parserTestSuite
from Tests.unitTests.testApiCalls import api_TestSuite, disableMock
from sys import argv
import unittest

"""
For running all tests or commenting out particular tests suites to only run selected tests.
"""

if __name__=="__main__":
	suiteList=[]

	if len(argv)>1:
		if argv[1]=="d":
			#disables mocking in testApiCalls
			#i.e the test will actually open a connection to the URL that it's given
			#instead of normally just mocking/faking the results from the connection
			disableMock()

	suiteList.append(offValidationTestSuite)
	suiteList.append(parserTestSuite)
	suiteList.append(api_TestSuite)


	fullSuite = unittest.TestSuite(suiteList)

	runner = unittest.TextTestRunner()
	runner.run(fullSuite)
