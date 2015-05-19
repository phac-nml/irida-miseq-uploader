from Tests.unitTests.testOfflineValidation import offValidationTestSuite
from Tests.unitTests.testMiseqParser import parserTestSuite
import unittest

"""
For running all tests or commenting out particular tests suites to only run selected tests.
"""

if __name__=="__main__":
	suiteList=[]
	
	suiteList.append(offValidationTestSuite)
	suiteList.append(parserTestSuite)
	
	fullSuite = unittest.TestSuite(suiteList)

	runner = unittest.TextTestRunner()
	runner.run(fullSuite)