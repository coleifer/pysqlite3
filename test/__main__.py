import optparse
import sys
import unittest

from test.backup import suite as backup_suite
from test.dbapi import suite as dbapi_suite
from test.factory import suite as factory_suite
from test.hooks import suite as hooks_suite
from test.regression import suite as regression_suite
from test.transactions import suite as transactions_suite
from test.ttypes import suite as types_suite
from test.userfunctions import suite as userfunctions_suite


def test(verbosity=1, failfast=False):
    runner = unittest.TextTestRunner(verbosity=verbosity, failfast=failfast)
    all_tests = unittest.TestSuite((
        backup_suite(),
        dbapi_suite(),
        factory_suite(),
        hooks_suite(),
        regression_suite(),
        transactions_suite(),
        types_suite(),
        userfunctions_suite()))
    results = runner.run(all_tests)
    return results.failures, results.errors


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-v', '--verbosity', default=1, dest='verbosity',
                      type='int', help='output verbosity, default=1')
    parser.add_option('-f', '--failfast', action='store_true', dest='failfast')
    options, args = parser.parse_args()

    failures, errors = test(options.verbosity, options.failfast)
    if failures or errors:
        sys.exit(1)
