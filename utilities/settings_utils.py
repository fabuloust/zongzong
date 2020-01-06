from django.conf import settings


def is_for_testcase():
    return getattr(settings, "IS_FOR_TESTCASE", False)
