# -*- coding: utf-8 -*-
"""

"""

from __future__ import absolute_import

import logging

import os
from stat import ST_DEV, ST_INO

__all__ = ["CustomWatchedFileHandler"]


class CustomWatchedFileHandler(logging.FileHandler):
    """
    配合logrotate(https://git.chunyu.me/feiwang/logrotate),
    监听log文件的大小的变化
    """

    def __init__(self, filename, mode='a', encoding=None, delay=0):
        logging.FileHandler.__init__(self, filename, mode, encoding, delay)
        if not os.path.exists(self.baseFilename):
            self.dev, self.ino = -1, -1
        else:
            stat = os.stat(self.baseFilename)
            self.dev, self.ino = stat[ST_DEV], stat[ST_INO]

    def emit(self, record):
        if not os.path.exists(self.baseFilename):
            stat = None
            changed = 1
        else:
            stat = os.stat(self.baseFilename)
            # http://pubs.opengroup.org/onlinepubs/009695399/basedefs/sys/stat.h.html
            # The st_ino and st_dev fields taken together uniquely identify the file within the system.
            changed = (stat[ST_DEV] != self.dev) or (stat[ST_INO] != self.ino)

        if changed and self.stream is not None:
            # 打开文件可能出错，因此每次判定是否已经关闭
            if not self.stream.closed:
                self.stream.flush()
                self.stream.close()

            # 重新打开文件
            self.stream = self._open()
            if stat is None:
                stat = os.stat(self.baseFilename)

            self.dev, self.ino = stat[ST_DEV], stat[ST_INO]

        # 交给系统默认的实现
        logging.FileHandler.emit(self, record)
