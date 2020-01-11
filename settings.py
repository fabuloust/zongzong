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

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '@lu_8lklf*-+=hiuz8udvx@m9ug))b71d9!i873guu(%qz3d!d'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'api',
    'footprint',
    'user_info',
    'weixin',
    'commercial',
    'chat',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'middlewares.elapsed_time.ElapsedTimeMiddleware',
]

ROOT_URLCONF = 'urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases



# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR + '/zongzong/static/'

REDIS = {
    'default': {
        'host': '127.0.0.1',
        'port': '6379',
        'password': '',
    }
}

BROKER_URL = 'redis://127.0.0.1:6379/0'

LOGS_BASE_DIR = BASE_DIR + '/zongzong/logs/'
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(levelname)s %(module)s.%(funcName)s Line:%(lineno)d  %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
        'raw': {
            'format': '%(message)s'
        },
    },

    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },

        # 默认的服务器Log(保存到log/filelog.log中, 通过linux的logrotate来处理日志的分割
        'default': {
            'level': 'INFO',
            'class': 'log_utils.handlers.custom_watched_file.CustomWatchedFileHandler',
            'filename': os.path.join(LOGS_BASE_DIR, 'filelog.log'),
            'formatter': 'verbose',
        },

        # 默认的服务器ERROR log
        'default_err': {
            'level': 'ERROR',
            'class': 'log_utils.handlers.custom_watched_file.CustomWatchedFileHandler',
            'filename': os.path.join(LOGS_BASE_DIR, 'error_logger.log'),
            'formatter': 'verbose',
        },

        'elapsed_hdl': {
            'level': 'INFO',
            'class': 'log_utils.handlers.custom_watched_file.CustomWatchedFileHandler',
            'filename': os.path.join(LOGS_BASE_DIR, 'elapsed_logger.log'),
            'formatter': 'verbose',
        },

    },

    'loggers': {
        # 默认都交给django了
        'django': {
            'handlers': ['default'],
            'propagate': True,
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['default_err'],
            'level': 'ERROR',
            'propagate': False,
        },

        'elapsed_logger': {
            'handlers': ['elapsed_hdl'],
            'level': 'INFO',
            'propagate': False,
        },

    },
    'root': {
        'level': 'INFO',
        'handlers': ['default'],
    },
}

USE_TZ = False
TIME_ZONE = 'Asia/Shanghai'
