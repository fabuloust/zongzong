#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
更新数据库，保证测试用例的准确性
"""

import hashlib
import os
import sys
import json
from os.path import normpath, dirname

PACKAGE_INFO_FILE_NAME = "package_info.txt"


PROJECT_ROOT = dirname(dirname(__file__))
PACKAGE_INFO_FILE_PATH = normpath(os.path.join(PROJECT_ROOT, "log/", PACKAGE_INFO_FILE_NAME))


def app_model_checksum(path):
    chksum = hashlib.md5()
    filepath = os.path.join(path, "models.py")

    if os.path.exists(filepath):
        chksum.update(open(filepath, "rb").read())

    return chksum.hexdigest()


def slqite3_md5():
    filepath = os.path.join(PROJECT_ROOT, "sqlite3.db")
    if os.path.exists(filepath):
        chksum = hashlib.md5()
        chksum.update(open(filepath, "rb").read())
        return chksum.hexdigest()
    else:
        return None


def rebuild_hash(paths):
    try:
        os.remove(PACKAGE_INFO_FILE_PATH)
    except:
        pass

    result = {}
    for path in paths:
        app_path = os.path.join(PROJECT_ROOT, path)

        result[app_path] = app_model_checksum(app_path)

    f = open(PACKAGE_INFO_FILE_PATH, "w")
    f.write(json.dumps(result))
    f.close()


def get_json_info():
    if not os.path.exists(PACKAGE_INFO_FILE_PATH):
        return {}

    try:
        package_info = json.loads(open(PACKAGE_INFO_FILE_PATH).read())
        return package_info
    except:
        return {}


def has_paths_changed(paths):
    """
    判断所有的App的Models的签名是否正确
    :param paths:
    :return:
    """
    package_info = get_json_info()
    if not package_info:
        rebuild_hash(paths)
        return True

    for path in paths:
        app_path = os.path.join(PROJECT_ROOT, path)
        app_hash = app_model_checksum(app_path)
        # 如果发现hash变化了，则重建数据库
        if package_info.get(app_path, '') != app_hash:
            rebuild_hash(paths)
            return True

    db_md5 = slqite3_md5()
    if package_info.get("db_md5", "") != db_md5:
        return True

    return False


if __name__ == "__main__":
    op = sys.argv[1]
    if op == "check":
        print 1 if has_paths_changed(sys.argv[2:]) else 0
    elif op == "rebuild":
        db_md5 = slqite3_md5()
        package_info = get_json_info()
        package_info["db_md5"] = db_md5 or ""
        f = open(PACKAGE_INFO_FILE_PATH, "w")
        f.write(json.dumps(package_info))
        f.close()

