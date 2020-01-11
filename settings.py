from settings_base import *

import pymysql
pymysql.install_as_MySQLdb()
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'zongzong',
        'USER': 'root',
        'PASSWORD': 'zongzong',
        'HOST': 'localhost',
        'PORT': '3306'
    }
}