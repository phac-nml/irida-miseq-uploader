import Tests.unitTests.test_OfflineValidation as test_OfflineValidation
import Tests.unitTests.test_MiseqParser as test_MiseqParser
import Tests.unitTests.test_ApiCalls as test_ApiCalls
import Tests.unitTests.test_IridaUploaderMain as test_IridaUploaderMain
import Tests.unitTests.test_SettingsFrame as test_SettingsFrame
import Tests.integrationTests.test_ApiCalls_integration as apiCalls_integration

import unittest
import platform
import argparse
import sys
from os import system, path, listdir, getcwd


"""
For running all tests or commenting out particular tests suites to only run
selected tests. 
"""


def load_integration_tests(suite_list):

    if platform.system() == "Linux":
        print "Loading integration tests"
        api_integ_ts = apiCalls_integration.load_test_suite()
        suite_list.append(api_integ_ts)


def load_unit_tests(suite_list):

    print "Loading unit tests"

    iu_main_ts = test_IridaUploaderMain.load_test_suite()
    suite_list.append(iu_main_ts)

    api_ts = test_ApiCalls.load_test_suite()
    suite_list.append(api_ts)

    miseq_ts = test_MiseqParser.load_test_suite()
    suite_list.append(miseq_ts)

    off_valid_ts = test_OfflineValidation.load_test_suite()
    suite_list.append(off_valid_ts)

    settings_ts = test_SettingsFrame.load_test_suite()
    suite_list.append(settings_ts)

if __name__ == "__main__":

    suite_list = []
    setup_handler = None
    exit_with_failure = False

    parser = argparse.ArgumentParser()
    parser.add_argument("--integration", action="store_true",
                        help="Run integration tests (can take a long time)")
    args = parser.parse_args()

    try:
        if args.integration:
            load_integration_tests(suite_list)

            print "Starting setup"
            setup_handler = apiCalls_integration.start_setup()

        load_unit_tests(suite_list)

        full_suite = unittest.TestSuite(suite_list)
        runner = unittest.TextTestRunner()
        test_result = runner.run(full_suite)

    # if **anything** fails, make sure we tear down IRIDA.
    except:
	if setup_handler is not None:
            setup_handler.stop_irida()
        sys.exit(1)

    if len(test_result.failures)>0 or len(test_result.errors)>0:
        sys.exit(1)
