import unittest

from test.backup import suite as backup_suite
from test.dbapi import suite as dbapi_suite
from test.factory import suite as factory_suite
from test.hooks import suite as hooks_suite
from test.regression import suite as regression_suite
from test.transactions import suite as transactions_suite
from test.types import suite as types_suite
from test.userfunctions import suite as userfunctions_suite


def test():
    runner = unittest.TextTestRunner()
    all_tests = unittest.TestSuite((
        backup_suite(),
        dbapi_suite(),
        factory_suite(),
        hooks_suite(),
        regression_suite(),
        transactions_suite(),
        types_suite(),
        userfunctions_suite()))
    runner.run(all_tests)


if __name__ == '__main__':
    test()
