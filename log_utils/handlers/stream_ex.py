# -*- coding: utf-8 -*-
"""

"""

from __future__ import absolute_import


import logging
import os

disable_print_function = False


class NullWriter(object):
    closed = False
    encoding = "utf-8"

    def write(self, *args, **kwargs): pass

    def writeln(self, *args, **kwargs): pass

    def close(self): pass

    def flush(self): pass

    def fileno(self):
        return 1

    def isatty(self):
        return False

    def writelines(self, liens):
        pass


class StreamHandlerEx(logging.StreamHandler):
    def __init__(self, stream=None):
        # 如果不需要日志，则输出到NullWriter中
        if disable_print_function or os.environ.get("disable_print_function"):
            if stream is None:
                stream = NullWriter()
        super(StreamHandlerEx, self).__init__(stream)
