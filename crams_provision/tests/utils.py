from itertools import chain, combinations

import unittest
import simplejson


class _ClassWithEquality:
    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return isinstance(other,
                          self.__class__) and self.__dict__ == other.__dict__

    # __eq__ does not seem to work inside functions. Check error message below:
    #    AssertionError:
    #      Expected call: add_user(<class 'nc_provision.tests.Tenant'>,
    # <class 'nc_provision.tests.User'>, <class 'nc_provision.tests.Role'>)
    #      Actual call:   add_user(<class 'nc_provision.tests.Tenant'>,
    # <class 'nc_provision.tests.User'>, <class 'nc_provision.tests.Role'>)
    #
    def __ne__(self, other):
        return not self == other


# A function to create objects on the fly.
#  - Pass object properties as a attributeDict,
# make sure the keys in the dict are enclosed in single quotes.
def get_dynamic_class(className, attributeDict):
    return type(className, (_ClassWithEquality,), attributeDict)


def get_power_set_as_list(aList):
    i = set(aList)
    retList = []
    for z in chain.from_iterable(
            combinations(i, r) for r in range(len(i) + 1)):
        retList.append(z)
    return retList


class ProvisionTestCase(unittest.TestCase):
    pass


class HttpMockResponse:
    @classmethod
    def get_response(self, status, data):
        return get_dynamic_class('MockResponse', {
            "status": status,
            "data": simplejson.dumps(data)
        })

    @classmethod
    def get_success_response(self, data):
        return self.get_response(200, data)

    @classmethod
    def get_bad_request_response(self):
        return self.get_response(400, None)
