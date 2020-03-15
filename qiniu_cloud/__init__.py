# -*- coding:utf-8 -*-

# 服务器上传使用的bucket, 即 chunyu-files
from qiniu_cloud.manager import QiniuCloudStorageManager

ServerBucket = QiniuCloudStorageManager(bucket='zongz', default_host='')
